"""Auditoria agregada do catálogo original; nenhuma seleção ou alteração de dados.

DuckDB mantém uma tabela textual em disco temporário e views analíticas. Só
agregados saem do banco. Os campos originais nunca são sobrescritos.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import yaml

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[2]
SOURCE_RELATIVE = Path("data/raw/spotify/spotify_data.csv")
QUANTILES = (0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
ACOUSTIC = (
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
    "time_signature",
)
PATTERNS = {
    "live": r"\blive\b|\bao vivo\b",
    "remaster": r"\bremaster(ed|izado|izada)?\b",
    "remix": r"\bremix(ed)?\b",
    "acoustic": r"\bacoustic\b|\bac[uú]stic[oa]\b|\bunplugged\b",
    "demo": r"\bdemo\b",
    "radio_edit": r"\bradio[ -]edit\b",
    "instrumental": r"\binstrumental\b",
    "mono_stereo": r"\b(mono|stereo)\b",
    "extended": r"\bextended\b",
    "karaoke": r"\bkaraoke\b",
}
LIMITATIONS = [
    "Catálogo acessível da fonte; não representa probabilisticamente todo o Spotify.",
    "Data de coleta da popularidade e significado preciso de year: não confirmado.",
    "Faixa Spotify é a unidade inicial; track_id não identifica composição ou gravação universal.",
    "Artistas e pares artista+título usam strings aparadas, sem separar colaborações ou homônimos.",
    "Gênero é a célula textual inteira; indícios de múltiplos rótulos não são divididos automaticamente.",
    "Flags de versão são heurísticas de palavras no título; admitem falsos positivos e negativos e se sobrepõem.",
    "Valores inválidos/ausentes continuam nas contagens; resumos numéricos válidos têm denominador próprio.",
    "track_id_sem_conflito é um subconjunto descritivo: IDs ausentes e conflitantes não são representados nele.",
    "LFM2b não condiciona elegibilidade; cobertura histórica do LRCLIB não é extrapolável para este catálogo.",
    "Teste V0.6 aberto em 2026-10-14T16:12:27.567600+00:00; novo sorteio não restaura independência.",
    "Futuros splits exigirão reconciliação com registros/grupos anteriores e agrupamento por artista e composição operacional.",
    "Nenhuma amostra, seed, split, letra, embedding ou modelo é produzido; resultados não são causais.",
]


def ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def clean(column: str) -> str:
    value = f"trim({ident(column)})"
    return f"CASE WHEN {value} IN ('', 'NA', 'N/A', 'null', 'None') THEN NULL ELSE {value} END"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def numeric_stats(expression: str) -> str:
    return ", ".join(
        [
            f"count({expression}) AS n_valid",
            f"min({expression}) AS min",
            f"max({expression}) AS max",
            f"avg({expression}) AS mean",
            f"stddev_samp({expression}) AS std_sample",
            f"median({expression}) AS median",
            *[f"quantile_cont({expression}, {q}) AS q{int(q * 100):02d}" for q in QUANTILES],
        ]
    )


def date_expression(column: str) -> str:
    """Somente ISO YYYY, YYYY-MM, YYYY-MM-DD; sem inferência pelo título."""
    c = clean(column)
    return (
        f"CASE WHEN regexp_full_match({c}, '[0-9]{{4}}') "
        f"THEN try_cast({c} || '-01-01' AS DATE) "
        f"WHEN regexp_full_match({c}, '[0-9]{{4}}-[0-9]{{2}}') "
        f"THEN try_cast({c} || '-01' AS DATE) "
        f"WHEN regexp_full_match({c}, '[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}') "
        f"THEN try_cast({c} AS DATE) END"
    )


def provenance(input_path: Path) -> dict[str, Any]:
    known = input_path == (ROOT / SOURCE_RELATIVE).resolve()
    result: dict[str, Any] = {"matches_configured_path": known}
    if not known:
        result["source_status"] = "Entrada alternativa/fixture: origem não confirmado."
        return result
    result.update(
        {
            "evidence": [
                "docs/provenance.md",
                "data/raw/manifest.json",
                "configs/data_sources.example.yaml",
                "src/tcc_music_popularity/acquisition.py",
            ],
            "url": "https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks",
            "license_documented": "Database: Open Database; Contents: © Original Authors",
            "upstream_updated_at_documented": "2023-06-21T12:27:55.677Z",
            "upstream_version": "não confirmado (não há número de versão registrado)",
            "download_date": "não confirmado: docs indicam 2026-08-18 UTC; manifesto registra reutilização",
            "popularity_collected_at": "não confirmado",
            "year_meaning": "não confirmado; não chamar de ano original de lançamento",
            "historical_rows_not_recounted": 1_159_764,
            "documented_sha256": "42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897",
            "transformations": "Código de aquisição extrai bytes do CSV do ZIP sem transformação; execução histórica não comprovada por isso. Normalização e matching são derivados separados e não entram nesta auditoria.",
        }
    )
    manifest = ROOT / "data/raw/manifest.json"
    if manifest.exists():
        source = (
            json.loads(manifest.read_text(encoding="utf-8")).get("sources", {}).get("spotify", {})
        )
        result["manifest_evidence"] = {
            key: source.get(key)
            for key in (
                "sha256",
                "size_bytes",
                "obtained_or_verified_at",
                "acquisition_method",
                "record_count",
            )
        }
    return result


class Audit:
    def __init__(self, con: duckdb.DuckDBPyConnection, summary: dict[str, Any]):
        self.con = con
        self.summary = summary
        self.long: list[dict[str, Any]] = []

    def query(self, sql: str) -> list[dict[str, Any]]:
        result = self.con.execute(sql)
        names = [c[0] for c in result.description]
        return [dict(zip(names, row, strict=True)) for row in result.fetchall()]

    def one(self, sql: str) -> dict[str, Any]:
        return self.query(sql)[0]

    def emit(
        self,
        scope: str,
        section: str,
        dimensions: dict[str, Any],
        metrics: dict[str, Any],
        denominator: int | None = None,
    ) -> None:
        pairs = list(dimensions.items())
        for metric, value in metrics.items():
            self.long.append(
                {
                    "scope": scope,
                    "section": section,
                    **{
                        f"dimension_{i + 1}": pairs[i][0] if len(pairs) > i else ""
                        for i in range(3)
                    },
                    **{f"value_{i + 1}": pairs[i][1] if len(pairs) > i else "" for i in range(3)},
                    "metric": metric,
                    "value": value,
                    "denominator": denominator,
                }
            )

    def load(self, path: Path) -> tuple[list[str], list[str]]:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream), [])
        columns = [name.strip().lower() or f"source_index_{i}" for i, name in enumerate(header)]
        required = {"track_id", "track_name", "artist_name", "popularity", "year", "genre"}
        missing = sorted(required - set(columns))
        if (
            missing
            or len(set(columns)) != len(columns)
            or any(c.startswith("audit_") for c in columns)
        ):
            raise ValueError(
                f"Schema incompatível: faltam {missing}; cabeçalhos devem ser únicos e não usar audit_. "
                "Forneça o CSV Spotify original (não a base integrada)."
            )
        schema = "{" + ",".join(f"{literal(c)}:'VARCHAR'" for c in columns) + "}"
        self.con.execute(
            f"CREATE TABLE raw AS SELECT * FROM read_csv({literal(str(path))}, "
            f"header=true, columns={schema}, auto_detect=false, delim=',', quote='\"', "
            "escape='\"', strict_mode=true, nullstr='', allow_quoted_nulls=false)"
        )
        n = self.one("SELECT count(*) AS n FROM raw")["n"]
        if not n:
            raise ValueError("CSV sem registros; não há população para descrever.")
        schema_stats = []
        for original, c in zip(header, columns, strict=True):
            x = f"try_cast({clean(c)} AS DOUBLE)"
            s = self.one(
                f"SELECT count(*) - count({clean(c)}) AS missing, "
                f"count({x}) AS numeric_parseable, "
                f"count(*) FILTER (WHERE isfinite({x}) AND {x} = trunc({x})) AS integer_parseable FROM raw"
            )
            present = n - s["missing"]
            inferred = "VARCHAR"
            if not present:
                inferred = "indeterminado (todos ausentes)"
            elif s["integer_parseable"] == present:
                inferred = "INTEGER"
            elif s["numeric_parseable"] == present:
                inferred = "DOUBLE (pode conter não finitos)"
            schema_stats.append(
                {
                    "original_header": original,
                    "column": c,
                    "storage_type": "VARCHAR (CSV textual preservado)",
                    "inferred_logical_type": inferred,
                    **s,
                    "missing_percent": 100 * s["missing"] / n,
                }
            )
            self.emit("linha", "schema", {"column": c}, s, n)
        self.summary["structure"] = {"rows": n, "columns": len(columns), "schema": schema_stats}
        indexes = [
            c
            for c, original in zip(columns, header, strict=True)
            if not original.strip() or c == "index" or c.startswith("unnamed:")
        ]
        substantive = [c for c in columns if c not in indexes]
        fields = ",".join(map(ident, substantive))
        self.con.execute(f"CREATE TABLE variants AS SELECT DISTINCT {fields} FROM raw")
        self.con.execute(
            f"CREATE TABLE id_counts AS SELECT {clean('track_id')} AS audit_id, "
            f"count(*) AS n FROM raw WHERE {clean('track_id')} IS NOT NULL GROUP BY 1"
        )
        self.con.execute(
            f"CREATE TABLE id_variants AS SELECT {clean('track_id')} AS audit_id, "
            f"count(*) AS n FROM variants WHERE {clean('track_id')} IS NOT NULL GROUP BY 1"
        )
        duplicates = self.one(
            "SELECT count(*) AS distinct_ids, count(*) FILTER (WHERE c.n > 1) AS repeated_ids, "
            "count(*) FILTER (WHERE c.n > 1 AND v.n = 1) AS repeated_equal_ids, "
            "count(*) FILTER (WHERE v.n > 1) AS conflicting_ids, "
            "coalesce(sum(c.n) FILTER (WHERE v.n > 1), 0) AS rows_conflicting_ids, "
            "coalesce(sum(c.n) FILTER (WHERE c.n > 1 AND v.n = 1), 0) AS rows_repeated_equal_ids, "
            "coalesce(sum(c.n - 1), 0) AS excess_rows_over_distinct_ids "
            "FROM id_counts c JOIN id_variants v USING(audit_id)"
        )
        duplicates.update(
            self.one(
                "SELECT coalesce(sum(n - 1), 0) AS exact_duplicate_excess_rows, "
                "coalesce(sum(n) FILTER (WHERE n > 1), 0) AS exact_duplicate_involved_rows "
                "FROM (SELECT count(*) AS n FROM raw GROUP BY "
                + ",".join(map(ident, columns))
                + ")"
            )
        )
        duplicates["substantive_duplicate_excess_rows"] = (
            n - self.one("SELECT count(*) AS n FROM variants")["n"]
        )
        duplicates["missing_id_rows"] = self.one(
            f"SELECT count(*) AS n FROM raw WHERE {clean('track_id')} IS NULL"
        )["n"]
        duplicates["consistent_ids"] = duplicates["distinct_ids"] - duplicates["conflicting_ids"]
        self.summary["duplicates"] = duplicates
        self.summary["ignored_index_columns_for_conflicts"] = indexes
        self.emit("linha", "duplicates", {}, duplicates)
        conflicts = {}
        for column in substantive:
            different = (
                f"count(DISTINCT {ident(column)}) + max(cast({ident(column)} IS NULL AS INTEGER))"
            )
            conflicts[column] = self.one(
                f"SELECT count(*) AS n FROM (SELECT {clean('track_id')} AS id FROM variants "
                f"WHERE {clean('track_id')} IS NOT NULL GROUP BY 1 HAVING {different} > 1)"
            )["n"]
            self.emit(
                "track_id",
                "conflicting_field",
                {"field": column},
                {"ids_with_conflict": conflicts[column]},
                duplicates["distinct_ids"],
            )
        self.summary["conflicts_by_field"] = conflicts
        self.con.execute(
            f"CREATE VIEW track_base AS SELECT v.* FROM variants v "
            f"JOIN id_variants i ON {clean('track_id')} = i.audit_id WHERE i.n = 1"
        )
        return columns, indexes

    def prepare(self, columns: list[str], rules: dict[str, Any]) -> tuple[list[str], str]:
        dates = [c for c in columns if re.search(r"(^|_)(year|date|timestamp)($|_)|_at$", c)]
        missing_acoustic = [c for c in ACOUSTIC if c not in columns]
        self.summary["absent_optional_acoustic_fields"] = missing_acoustic
        if missing_acoustic:
            self.summary["alerts"].append(
                "Atributos acústicos opcionais ausentes: " + ", ".join(missing_acoustic)
            )
        self.summary["temporal_fields"] = {
            c: {
                "origin": f"Coluna original do CSV: {c}",
                "meaning": "não confirmado",
                "parser": "ISO YYYY, YYYY-MM, YYYY-MM-DD; precisão mantida em contagens separadas",
                "valid_year_range_local_rule": rules["year"],
            }
            for c in dates
        }
        lo, hi = rules["year"]
        expressions = [
            f"{clean('track_id')} AS audit_id",
            f"{clean('artist_name')} AS audit_artist",
            f"{clean('track_name')} AS audit_title",
            f"{clean('genre')} AS audit_genre",
        ]
        for c in ["popularity", *[x for x in ACOUSTIC if x in columns]]:
            expressions.append(f"try_cast({clean(c)} AS DOUBLE) AS {ident('audit_num_' + c)}")
        for c in dates:
            parsed = date_expression(c)
            expressions.append(
                f"CASE WHEN year({parsed}) BETWEEN {lo} AND {hi} "
                f"THEN {parsed} END AS {ident('audit_date_' + c)}"
            )
        for c, pattern in PATTERNS.items():
            expressions.append(
                f"coalesce(regexp_matches(lower({clean('track_name')}), "
                f"{literal(pattern)}), false) AS audit_flag_{c}"
            )
        pop = "audit_num_popularity"
        valid = f"isfinite({pop}) AND {pop} BETWEEN 0 AND 100 AND {pop} = trunc({pop})"
        decade = "cast(cast(floor(year(audit_date_year) / 10) * 10 AS INTEGER) AS VARCHAR)"
        for source, target in [("raw", "rows"), ("track_base", "tracks")]:
            self.con.execute(
                f"CREATE VIEW {target}_parsed AS SELECT *, {','.join(expressions)} FROM {source}"
            )
            self.con.execute(
                f"CREATE VIEW {target} AS SELECT *, CASE WHEN {valid} THEN {pop} END AS audit_pop, "
                f"CASE WHEN {valid} THEN CASE WHEN {pop} >= 90 THEN '90–100' ELSE "
                f"cast(cast(floor({pop}/10)*10 AS INTEGER) AS VARCHAR) || '–' || "
                f"cast(cast(floor({pop}/10)*10+9 AS INTEGER) AS VARCHAR) END "
                f"WHEN {clean('popularity')} IS NULL THEN '[ausente]' ELSE '[inválido]' END AS audit_pop_band, "
                f"CASE WHEN audit_date_year IS NOT NULL THEN {decade} || '–' || "
                f"cast(cast(floor(year(audit_date_year)/10)*10+9 AS INTEGER) AS VARCHAR) "
                f"WHEN {clean('year')} IS NULL THEN '[ausente]' ELSE '[inválido]' END AS audit_period "
                f"FROM {target}_parsed"
            )
        return dates, "year"

    def grouped(
        self, table: str, scope: str, section: str, dimensions: dict[str, str]
    ) -> list[dict[str, Any]]:
        selection = ", ".join(
            f"{expression} AS {ident(name)}" for name, expression in dimensions.items()
        )
        order = ",".join(str(i + 1) for i in range(len(dimensions)))
        rows = self.query(
            f"SELECT {selection}, count(*) AS n, {numeric_stats('audit_pop')} "
            f"FROM {table} GROUP BY {order} ORDER BY {order}"
        )
        total = self.one(f"SELECT count(*) AS n FROM {table}")["n"]
        if section == "popularity_band":
            # Publicar também os intervalos de frequência zero, inclusive 90–100.
            bands = [f"{i}–{i + 9}" for i in range(0, 90, 10)] + ["90–100"]
            observed = {row["band"]: row for row in rows}
            empty = {
                "n": 0,
                "n_valid": 0,
                "min": None,
                "max": None,
                "mean": None,
                "std_sample": None,
                "median": None,
                **{f"q{int(q * 100):02d}": None for q in QUANTILES},
            }
            rows = [observed.get(band, {"band": band, **empty}) for band in bands]
            rows += [observed[band] for band in ("[ausente]", "[inválido]") if band in observed]
        for row in rows:
            row["fraction"] = row["n"] / total if total else None
            self.emit(
                scope,
                section,
                {c: row[c] for c in dimensions},
                {k: v for k, v in row.items() if k not in dimensions},
                total,
            )
        return rows

    def describe(
        self, table: str, scope: str, columns: list[str], dates: list[str], rules: dict[str, Any]
    ) -> dict[str, Any]:
        n = self.one(f"SELECT count(*) AS n FROM {table}")["n"]
        result: dict[str, Any] = {"n": n}
        result["identity"] = self.one(
            f"SELECT count(DISTINCT audit_artist) AS distinct_artist_strings, "
            "count(DISTINCT (audit_artist, audit_title)) FILTER (WHERE audit_artist IS NOT NULL "
            "AND audit_title IS NOT NULL) AS distinct_complete_artist_title_pairs, "
            "count(*) FILTER (WHERE audit_artist IS NULL) AS missing_artist, "
            f"count(*) FILTER (WHERE audit_artist IS NULL OR audit_title IS NULL) AS incomplete_pairs FROM {table}"
        )
        self.emit(scope, "identity", {}, result["identity"], n)
        result["popularity"] = self.one(
            f"SELECT {numeric_stats('audit_pop')}, count(*) FILTER (WHERE {clean('popularity')} IS NULL) AS missing, "
            f"count(*) FILTER (WHERE {clean('popularity')} IS NOT NULL AND audit_pop IS NULL) AS invalid, "
            f"count(*) FILTER (WHERE audit_pop = 0) AS zero_count FROM {table}"
        )
        pop = result["popularity"]
        pop["zero_fraction_all"] = pop["zero_count"] / n if n else None
        pop["zero_fraction_valid"] = pop["zero_count"] / pop["n_valid"] if pop["n_valid"] else None
        pop["thresholds_overlapping"] = {
            str(threshold): self.one(
                f"SELECT count(*) AS n FROM {table} WHERE audit_pop >= {threshold}"
            )["n"]
            for threshold in (60, 70, 80, 90)
        }
        self.emit(
            scope, "popularity", {}, {k: v for k, v in pop.items() if not isinstance(v, dict)}, n
        )
        for threshold, count in pop["thresholds_overlapping"].items():
            self.emit(
                scope, "popularity_threshold_overlapping", {"gte": threshold}, {"n": count}, n
            )
        result["popularity_bands"] = self.grouped(
            table, scope, "popularity_band", {"band": "audit_pop_band"}
        )
        result["time"] = {}
        for c in dates:
            d = ident("audit_date_" + c)
            stats = self.one(
                f"SELECT cast(min({d}) AS VARCHAR) AS min_date, cast(max({d}) AS VARCHAR) AS max_date, "
                f"min(year({d})) AS min_year, max(year({d})) AS max_year, "
                f"count(*) FILTER (WHERE {clean(c)} IS NULL) AS missing, "
                f"count(*) FILTER (WHERE {clean(c)} IS NOT NULL AND {d} IS NULL) AS invalid, "
                f"count(*) FILTER (WHERE year({d}) >= 2020) AS since_2020 FROM {table}"
            )
            precision = self.query(
                f"SELECT CASE WHEN {d} IS NULL THEN '[ausente/inválido]' "
                f"WHEN length({clean(c)}) = 4 THEN 'ano' WHEN length({clean(c)}) = 7 THEN 'mês' "
                f"ELSE 'dia' END AS precision, count(*) AS n FROM {table} GROUP BY 1 ORDER BY 1"
            )
            self.emit(scope, "time_quality", {"field": c}, stats, n)
            for p in precision:
                self.emit(
                    scope,
                    "time_precision",
                    {"field": c, "precision": p["precision"]},
                    {"n": p["n"]},
                    n,
                )
            annual = self.grouped(
                table,
                scope,
                "annual_" + c,
                {"year": f"coalesce(cast(year({d}) AS VARCHAR), '[ausente/inválido]')"},
            )
            result["time"][c] = {**stats, "precision": precision, "annual": annual}
        result["periods"] = self.grouped(table, scope, "period", {"period": "audit_period"})
        result["genres"] = self.grouped(
            table, scope, "genre", {"genre": "coalesce(audit_genre, '[ausente]')"}
        )
        genre_info = self.one(
            f"SELECT count(*) FILTER (WHERE audit_genre IS NULL) AS missing, "
            "count(*) FILTER (WHERE regexp_matches(audit_genre, '[,;|\\[\\]]')) AS multi_label_hint_rows, "
            f"count(DISTINCT audit_genre) AS distinct_cells FROM {table}"
        )
        genre_info["representation"] = (
            "Uma célula textual por linha; múltiplos rótulos sem semântica confirmada."
        )
        if table == "rows":
            genre_info.update(
                self.one(
                    "SELECT count(*) FILTER (WHERE n_genres > 1) AS ids_with_multiple_genre_cells "
                    "FROM (SELECT audit_id, count(DISTINCT audit_genre) AS n_genres "
                    "FROM rows WHERE audit_id IS NOT NULL GROUP BY audit_id)"
                )
            )
        result["genre_structure"] = genre_info
        self.emit(
            scope,
            "genre_structure",
            {},
            {k: v for k, v in genre_info.items() if isinstance(v, int)},
            n,
        )
        counts = f"SELECT audit_artist, count(*) AS n FROM {table} WHERE audit_artist IS NOT NULL GROUP BY 1"
        result["artist_track_count_summary"] = self.one(
            f"SELECT {numeric_stats('n')} FROM ({counts})"
        )
        self.emit(scope, "artist_track_count_summary", {}, result["artist_track_count_summary"])
        result["artist_frequency_distribution"] = self.query(
            f"SELECT n AS tracks_or_rows_per_artist, count(*) AS artists "
            f"FROM ({counts}) GROUP BY n ORDER BY n"
        )
        for row in result["artist_frequency_distribution"]:
            self.emit(
                scope,
                "artist_frequency",
                {"tracks_or_rows": row["tracks_or_rows_per_artist"]},
                {"artists": row["artists"]},
            )
        total_known = n - result["identity"]["missing_artist"]
        artists = result["identity"]["distinct_artist_strings"]
        result["artist_concentration"] = []
        for top in (1, 10, 100, 1000):
            count = self.one(
                f"SELECT coalesce(sum(n), 0) AS n FROM (SELECT n FROM ({counts}) ORDER BY n DESC LIMIT {top})"
            )["n"]
            item = {
                "top_requested": top,
                "artists_included": min(top, artists),
                "n": count,
                "fraction_known_artist": count / total_known if total_known else None,
                "fraction_all": count / n if n else None,
            }
            result["artist_concentration"].append(item)
            self.emit(
                scope,
                "artist_concentration",
                {"top": top},
                {k: v for k, v in item.items() if k != "top_requested"},
                total_known,
            )
        result["versions"] = {}
        for flag, pattern in PATTERNS.items():
            count = self.one(f"SELECT count(*) AS n FROM {table} WHERE audit_flag_{flag}")["n"]
            result["versions"][flag] = {
                "n": count,
                "fraction": count / n if n else None,
                "origin": "regex no título original, após lower/trim",
                "regex": pattern,
            }
            self.emit(
                scope,
                "version_heuristic",
                {"flag": flag},
                {"n": count, "fraction": count / n if n else None},
                n,
            )
        result["acoustic"] = {}
        for c in ACOUSTIC:
            if c not in columns:
                continue
            x = ident("audit_num_" + c)
            domain = "true"
            domain_label = "Sem limites documentados; apenas parse/valor finito verificados."
            if c in rules["unit_interval"]:
                domain, domain_label = f"{x} BETWEEN 0 AND 1", "[0, 1]"
            elif c + "_values" in rules:
                values = rules[c + "_values"]
                domain, domain_label = f"{x} IN ({','.join(map(str, values))})", str(values)
            elif c + "_min_exclusive" in rules:
                minimum = rules[c + "_min_exclusive"]
                domain, domain_label = f"{x} > {minimum}", f"> {minimum}"
            finite = f"CASE WHEN isfinite({x}) THEN {x} END"
            valid = f"CASE WHEN isfinite({x}) AND {domain} THEN {x} END"
            quality = self.one(
                f"SELECT count(*) FILTER (WHERE {clean(c)} IS NULL) AS missing, "
                f"count(*) FILTER (WHERE {clean(c)} IS NOT NULL AND ({x} IS NULL OR NOT isfinite({x}))) AS nonnumeric_or_nonfinite, "
                f"count(*) FILTER (WHERE isfinite({x}) AND NOT ({domain})) AS out_of_domain FROM {table}"
            )
            stats = self.one(f"SELECT {numeric_stats(valid)} FROM {table}")
            observed = self.one(f"SELECT {numeric_stats(finite)} FROM {table}")
            result["acoustic"][c] = {
                "domain": domain_label,
                "domain_origin": "configs/quality_rules.yaml (regra local; não validação externa)",
                **quality,
                "valid_summary": stats,
                "all_finite_summary": observed,
            }
            self.emit(scope, "acoustic_quality", {"field": c}, quality, n)
            self.emit(scope, "acoustic_valid", {"field": c}, stats, n)
            self.emit(scope, "acoustic_all_finite", {"field": c}, observed, n)
        result["period_genre"] = self.grouped(
            table,
            scope,
            "period_genre",
            {"period": "audit_period", "genre": "coalesce(audit_genre, '[ausente]')"},
        )
        result["period_popularity"] = self.grouped(
            table, scope, "period_popularity", {"period": "audit_period", "band": "audit_pop_band"}
        )
        result["period_genre_popularity"] = self.grouped(
            table,
            scope,
            "period_genre_popularity",
            {
                "period": "audit_period",
                "genre": "coalesce(audit_genre, '[ausente]')",
                "band": "audit_pop_band",
            },
        )
        return result


def candidate_cells(rows: list[dict[str, Any]], keys: list[str]) -> dict[str, Any]:
    """Sparsidade é diagnóstico, nunca dimensionamento de amostra."""
    sizes = [r["n"] for r in rows]
    possible = 1
    for key in keys:
        possible *= len({r[key] for r in rows})
    return {
        "dimensions": keys,
        "observed_cells": len(sizes),
        "cartesian_cells": possible,
        "empty_cartesian_cells": possible - len(sizes),
        "population": sum(sizes),
        "min_cell": min(sizes, default=None),
        "max_cell": max(sizes, default=None),
        "cells_lt_5": sum(n < 5 for n in sizes),
        "cells_lt_20": sum(n < 20 for n in sizes),
        "units_in_cells_lt_20": sum(n for n in sizes if n < 20),
        "note": "Produto cartesiano das categorias marginais observadas, incluindo ausentes/inválidos; limiares 5 e 20 são diagnósticos, não regras de elegibilidade.",
    }


def plots(summary: dict[str, Any], output: Path) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    data = summary["scopes"]["track_id_sem_conflito"]
    label = "track_id sem conflito"
    if not data["n"]:
        data = summary["scopes"]["linha"]
        label = "linhas (nenhum ID sem conflito)"
    plans = [
        ("popularidade", "Popularidade", data["popularity_bands"], "band", "n", "Contagem"),
        (
            "ano",
            "Ano informado (sem semântica confirmada)",
            data["time"]["year"]["annual"],
            "year",
            "n",
            "Contagem",
        ),
        (
            "genero",
            "20 gêneros mais frequentes",
            sorted(data["genres"], key=lambda r: -r["n"])[:20],
            "genre",
            "n",
            "Contagem",
        ),
        (
            "concentracao_artista",
            "Concentração por artista (sem nomes)",
            data["artist_concentration"],
            "top_requested",
            "fraction_known_artist",
            "Fração com artista conhecido",
        ),
        (
            "versoes",
            "Indicadores de versão (sobrepostos)",
            [{"flag": k, **v} for k, v in data["versions"].items()],
            "flag",
            "n",
            "Contagem",
        ),
        (
            "popularidade_periodo",
            "Popularidade por período: mediana e P25–P75",
            data["periods"],
            "period",
            "median",
            "Popularidade válida",
        ),
    ]
    files = []
    for slug, title, rows, key, value, ylabel in plans:
        fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")
        labels = [str(r[key]) for r in rows]
        values = [r[value] if r[value] is not None else float("nan") for r in rows]
        if slug == "genero":
            ax.barh(labels[::-1], values[::-1], color="#376c8a")
            ax.set_xlabel(ylabel)
        else:
            ax.bar(range(len(rows)), values, color="#376c8a")
            ax.set_xticks(range(len(rows)), labels, rotation=60, ha="right")
            if len(rows) > 35:
                for i, tick in enumerate(ax.get_xticklabels()):
                    tick.set_visible(i % max(1, len(rows) // 20) == 0)
            if slug == "popularidade_periodo":
                for i, row in enumerate(rows):
                    if row["n_valid"]:
                        ax.plot([i, i], [row["q25"], row["q75"]], color="#c87825", linewidth=3)
                    else:
                        ax.text(i, 2, "sem valores\nválidos", ha="center", fontsize=8)
                ax.set_ylim(0, 105)
            # Barras NaN não participam do autoscale; manter categorias sem valores.
            ax.set_xlim(-0.6, max(len(rows) - 0.4, 0.6))
            if slug == "concentracao_artista":
                ax.set_xlabel("Artistas mais frequentes (top N, limitado aos disponíveis)")
            ax.set_ylabel(ylabel)
        ax.set_title(f"{title}\nBase: {label}; N = {data['n']:,}")
        filename = f"{slug}.png"
        fig.savefig(output / filename, dpi=150)
        plt.close(fig)
        files.append(filename)
    return files


def markdown_table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    def cell(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")

    return "\n".join(
        [
            "| " + " | ".join(keys) + " |",
            "| " + " | ".join(["---"] * len(keys)) + " |",
            *["| " + " | ".join(cell(row.get(k)) for k in keys) + " |" for row in rows],
        ]
    )


def report(summary: dict[str, Any]) -> str:
    sections = [
        "# Auditoria descritiva do catálogo Spotify",
        "",
        f"Entrada: `{summary['input']['path']}`. Execução: {summary['started_at']}.",
        "## Fonte e alcance",
        json.dumps(summary["provenance"], ensure_ascii=False, indent=2).join(
            ["```json\n", "\n```"]
        ),
        "## Estrutura, unidade e duplicações",
        f"{summary['structure']['rows']:,} linhas; {summary['structure']['columns']} colunas. Tipos físicos são textuais (CSV); numeric_parseable informa conversibilidade, sem substituir os originais.",
        markdown_table(
            summary["structure"]["schema"],
            ["column", "inferred_logical_type", "missing", "missing_percent", "numeric_parseable"],
        ),
        markdown_table(
            [{"metric": k, "n": v} for k, v in summary["duplicates"].items()], ["metric", "n"]
        ),
        "IDs com divergência por campo (contagens sobrepostas; não somar):",
        markdown_table(
            [{"field": k, "conflicting_ids": v} for k, v in summary["conflicts_by_field"].items()],
            ["field", "conflicting_ids"],
        ),
        f"Índices ignorados SOMENTE na igualdade substantiva: {summary['ignored_index_columns_for_conflicts']}. Igualdade exata compara todos os campos lidos do CSV, inclusive índice; não compara bytes de aspas/terminadores.",
        "`linha` mantém tudo. `track_id_sem_conflito` conta uma vez cada ID cujo registro substantivo é idêntico, sem escolher maior popularidade. IDs conflitantes e ausentes permanecem na base por linha; não há arquivo de rejeitados nem resolução de conflitos. Proposta pendente: investigar a fonte dos conflitos antes de construir a moldura amostral. Não escolher representante até definir regra independente do alvo.",
    ]
    for scope, data in summary["scopes"].items():
        sections += [
            f"## Base {scope}: N = {data['n']:,}",
            "### Identidade, artistas e pares",
            markdown_table([data["identity"]], list(data["identity"])),
            "### Popularidade Spotify",
            markdown_table(
                [{k: v for k, v in data["popularity"].items() if not isinstance(v, dict)}],
                [
                    "n_valid",
                    "missing",
                    "invalid",
                    "mean",
                    "std_sample",
                    "median",
                    "q01",
                    "q05",
                    "q25",
                    "q75",
                    "q95",
                    "q99",
                    "zero_count",
                    "zero_fraction_valid",
                    "zero_fraction_all",
                ],
            ),
            "Domínio: inteiros 0–100; inválidos não entram nos momentos. Frações usam o denominador nomeado; desvio-padrão amostral (n−1).",
            markdown_table(data["popularity_bands"], ["band", "n", "fraction"]),
            "Limiares cumulativos, sobrepostos (não somar): "
            + json.dumps(data["popularity"]["thresholds_overlapping"]),
            "### Tempo",
        ]
        for field, values in data["time"].items():
            sections += [
                f"Campo `{field}`: origem CSV; significado não confirmado. Datas parciais são ancoradas em janeiro/dia 1 apenas para cálculo; não indicam precisão diária.",
                markdown_table(
                    [values],
                    [
                        "min_date",
                        "max_date",
                        "min_year",
                        "max_year",
                        "missing",
                        "invalid",
                        "since_2020",
                    ],
                ),
                markdown_table(values["precision"], ["precision", "n"]),
                markdown_table(
                    values["annual"],
                    [
                        "year",
                        "n",
                        "n_valid",
                        "mean",
                        "median",
                        "q01",
                        "q05",
                        "q25",
                        "q75",
                        "q95",
                        "q99",
                    ],
                ),
            ]
        sections += [
            "Décadas do campo year (incluem anos 2020 em diante; sem corte em 2023):",
            markdown_table(
                data["periods"], ["period", "n", "n_valid", "mean", "median", "q25", "q75"]
            ),
            "### Gêneros e concentração",
            str(data["genre_structure"]),
            markdown_table(
                data["genres"],
                ["genre", "n", "fraction", "n_valid", "mean", "median", "q25", "q75"],
            ),
            "Distribuição de faixas/linhas por string de artista (nomes não publicados):",
            markdown_table(
                [data["artist_track_count_summary"]],
                ["n_valid", "min", "max", "mean", "median", "q25", "q75", "q95", "q99"],
            ),
            markdown_table(
                data["artist_concentration"],
                ["top_requested", "artists_included", "n", "fraction_known_artist", "fraction_all"],
            ),
            "### Versões e acústica",
            "Flags de título sobrepostas; nenhuma versão é excluída.",
            markdown_table(
                [{"flag": k, **v} for k, v in data["versions"].items()],
                ["flag", "n", "fraction", "regex"],
            ),
            markdown_table(
                [
                    {
                        "field": k,
                        "domain": v["domain"],
                        "missing": v["missing"],
                        "invalid_parse": v["nonnumeric_or_nonfinite"],
                        "out_of_domain": v["out_of_domain"],
                        **v["valid_summary"],
                    }
                    for k, v in data["acoustic"].items()
                ],
                [
                    "field",
                    "domain",
                    "missing",
                    "invalid_parse",
                    "out_of_domain",
                    "n_valid",
                    "min",
                    "max",
                    "mean",
                    "median",
                    "q01",
                    "q05",
                    "q25",
                    "q75",
                    "q95",
                    "q99",
                ],
            ),
            "Domínios acústicos vêm das regras locais registradas; loudness não tem limite numérico documentado. JSON/CSV também resumem todos os valores finitos, inclusive fora do domínio.",
            "Cruzamentos período × gênero, período × faixa de popularidade e triplo: contagens e métricas completas no JSON/CSV; células observadas abaixo no diagnóstico amostral.",
        ]
    sections += [
        "## Planejamento amostral preliminar",
        "A população acessível é o catálogo fornecido. A moldura candidata por ID sem conflito é provisória: ausências/conflitos precisam de decisão explícita; disponibilidade de letra não define elegibilidade do catálogo.",
        "Faixa é o objeto identificado por track_id; gravação pode reaparecer em múltiplas faixas/edições; composição operacional é um agrupamento futuro e imperfeito, nunca uma identidade universal. Pares textuais não provam identidade de composição.",
        markdown_table(
            [{**v, "candidate": k} for k, v in summary["sampling"].items()],
            [
                "candidate",
                "population",
                "observed_cells",
                "cartesian_cells",
                "empty_cartesian_cells",
                "min_cell",
                "max_cell",
                "cells_lt_5",
                "cells_lt_20",
                "units_in_cells_lt_20",
            ],
        ),
        "Proposta: amostragem aleatória estratificada sem reposição, inicialmente período × gênero, alocação proporcional n_h ≈ n·N_h/N. Fixar seed uma única vez no protocolo, sem procurar o melhor equilíbrio. Não se define n nesta etapa.",
        "Tamanhos de cada célula estão no CSV/JSON. Células <5/<20 são sinais descritivos, não limiares de poder. Se houver esparsidade, considerar períodos mais largos/agrupamento justificável de gêneros; só incorporar faixa de popularidade se o cruzamento triplo comportar a alocação pretendida. Grupos raros podem exigir sobreamostragem deliberada, com probabilidades de inclusão e pesos registrados; não impor cotas iguais automaticamente.",
        *[
            f"Diagnóstico {name}: {cells['observed_cells']} células observadas, "
            f"{cells['cells_lt_20']} com menos de 20 unidades "
            f"({cells['units_in_cells_lt_20']} de {cells['population']} unidades). "
            + (
                "Revisar simplificação/sobreamostragem antes de fixar alocação."
                if cells["cells_lt_20"]
                else "Ausência deste sinal não garante alocação suficiente; tamanho da amostra ainda pendente."
            )
            for name, cells in summary["sampling"].items()
        ],
        "Não selecionar por PCA/k-means, não usar margem de erro de proporções como garantia para aprendizagem de máquina. Decidir tamanho e simplificação dos estratos após examinar resultados e objetivo preditivo.",
        "Separar três etapas: (1) sorteio do catálogo; (2) disponibilidade/aceitação de letras e diagnóstico de perdas; (3) divisão de desenvolvimento/teste, agrupada por artista e composição operacional, reconciliada com o estudo anterior. A cobertura histórica LRCLIB na interseção LFM2b não é transportada para este catálogo.",
        "O teste V0.6 já foi aberto; um novo sorteio não restaura automaticamente a independência. Nenhum split foi criado ou alterado.",
        "## Alertas e limitações",
        *[f"- {text}" for text in summary["alerts"] + summary["limitations"]],
        "## Gráficos",
        *[f"![{name}]({name})" for name in summary.get("plots", [])],
        "## Leitura das saídas",
        "JSON: estrutura completa, proveniência, escopos, regras e status. CSV longo: scope, section, até três dimensões e uma métrica por linha; denominator é a população da distribuição, enquanto n_valid indica quantos valores válidos entraram nos momentos. fraction está em 0–1. Campos sem valor ficam vazios; não equivalem a zero. Nenhuma linha individual, título, ID ou letra é exportada.",
    ]
    return "\n\n".join(sections) + "\n"


def run(input_path: Path, output: Path, command: list[str] | None = None) -> dict[str, Any]:
    input_path, output = input_path.resolve(), output.resolve()
    if not input_path.is_file() or input_path.suffix.lower() != ".csv":
        raise ValueError("--input deve apontar para o arquivo CSV Spotify original existente.")
    if output.exists():
        raise ValueError(
            "--output já existe. Escolha uma pasta nova para preservar resultados anteriores."
        )
    if output == input_path.parent or output.is_relative_to(ROOT / "data"):
        raise ValueError(
            "Escolha uma pasta de relatórios nova, fora de data/ e da pasta de entrada."
        )
    output.mkdir(parents=True)
    started = time.perf_counter()
    stat = input_path.stat()
    summary: dict[str, Any] = {
        "status": "incomplete",
        "completed": False,
        "started_at": datetime.now(UTC).isoformat(),
        "code_version": VERSION,
        "code_sha256": sha256(Path(__file__)),
        "wrapper_sha256": sha256(ROOT / "scripts/11_auditar_catalogo_spotify.py"),
        "runtime": {"python": sys.version, "duckdb": duckdb.__version__},
        "command_argv": command if command is not None else [sys.executable, *sys.argv],
        "input": {"path": str(input_path), "size_bytes": stat.st_size},
        "provenance": {},
        "alerts": [],
        "limitations": LIMITATIONS.copy(),
    }
    json_path = output / "resumo_catalogo_spotify.json"

    def save() -> None:
        summary["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        pending = json_path.with_suffix(".json.tmp")
        pending.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
        )
        pending.replace(json_path)

    save()
    try:
        try:
            summary["git_head"] = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            summary["git_head"] = "não confirmado; use code_sha256"
        print("[1/6] Identificando arquivo e regras locais...", flush=True)
        summary["provenance"] = provenance(input_path)
        summary["input"]["sha256"] = sha256(input_path)
        expected = summary["provenance"].get("documented_sha256")
        if expected and summary["input"]["sha256"] != expected:
            summary["alerts"].append(
                "SHA-256 difere do documento histórico: não transportar contagens/proveniência como verificados para este arquivo."
            )
        rules_path = ROOT / "configs/quality_rules.yaml"
        rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))["spotify"]
        summary["quality_rules"] = {
            "path": str(rules_path),
            "sha256": sha256(rules_path),
            "rules": rules,
        }
        summary["missing_tokens_after_trim"] = ["", "NA", "N/A", "null", "None"]
        summary["version_heuristics"] = PATTERNS
        with (
            tempfile.TemporaryDirectory(prefix=".catalog_audit_", dir=output) as temporary,
            duckdb.connect(str(Path(temporary) / "audit.duckdb")) as con,
        ):
            con.execute("SET memory_limit='1GB'")
            con.execute("SET threads=2")
            con.execute("SET preserve_insertion_order=false")
            con.execute(f"SET temp_directory={literal(str(Path(temporary) / 'spill'))}")
            audit = Audit(con, summary)
            print("[2/6] Lendo CSV e quantificando duplicações (pode demorar)...", flush=True)
            columns, _ = audit.load(input_path)
            dates, _ = audit.prepare(columns, rules)
            summary["scopes"] = {}
            for index, (table, scope) in enumerate(
                [("rows", "linha"), ("tracks", "track_id_sem_conflito")], 3
            ):
                print(f"[{index}/6] Calculando distribuições: {scope}...", flush=True)
                summary["scopes"][scope] = audit.describe(table, scope, columns, dates, rules)
                save()
            tracks = summary["scopes"]["track_id_sem_conflito"]
            summary["sampling"] = {
                "period_genre": candidate_cells(tracks["period_genre"], ["period", "genre"]),
                "period_genre_popularity": candidate_cells(
                    tracks["period_genre_popularity"], ["period", "genre", "band"]
                ),
            }
            for candidate, cells in summary["sampling"].items():
                audit.emit(
                    "track_id_sem_conflito",
                    "sampling_cells",
                    {"candidate": candidate},
                    {k: v for k, v in cells.items() if isinstance(v, int) or v is None},
                )
            print("[5/6] Gravando tabelas agregadas e seis gráficos...", flush=True)
            with (output / "distribuicoes_catalogo_spotify.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as stream:
                writer = csv.DictWriter(stream, fieldnames=list(audit.long[0]))
                writer.writeheader()
                writer.writerows(audit.long)
        if summary["duplicates"]["conflicting_ids"]:
            summary["alerts"].append(
                "Há IDs conflitantes: a base por ID sem conflito não é o catálogo completo. Resolver a moldura antes do sorteio."
            )
        if not summary["scopes"]["track_id_sem_conflito"]["n"]:
            summary["alerts"].append(
                "Nenhum ID sem conflito; gráficos usam linhas. Planejamento por ID não disponível."
            )
        if summary["scopes"]["linha"]["genre_structure"]["multi_label_hint_rows"]:
            summary["alerts"].append(
                "Há células com indícios de múltiplos gêneros; revisar representação antes de estratificar."
            )
        summary["plots"] = plots(summary, output)
        final_stat = input_path.stat()
        if (stat.st_size, stat.st_mtime_ns) != (final_stat.st_size, final_stat.st_mtime_ns):
            raise RuntimeError(
                "Arquivo de entrada mudou durante a execução; resultados incompletos."
            )
        print("[6/6] Finalizando relatório e status...", flush=True)
        (output / "auditoria_catalogo_spotify.md").write_text(report(summary), encoding="utf-8")
        summary["completed"] = True
        summary["status"] = "completed"
        summary["finished_at"] = datetime.now(UTC).isoformat()
    except BaseException as exc:
        # Não publicar mensagens de parser que possam incluir uma linha individual.
        summary["error_type"] = type(exc).__name__
        summary["error"] = (
            str(exc)
            if isinstance(exc, (ValueError, RuntimeError))
            else "Falha de leitura/cálculo/saída; confira CSV UTF-8, esquema, memória e espaço em disco."
        )
        summary["alerts"].append(
            "Execução incompleta: não interpretar saídas parciais como auditoria final."
        )
        raise
    finally:
        save()
    return summary


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Auditoria agregada offline do CSV Spotify original; não sorteia amostra."
    )
    parser.add_argument("--input", type=Path, required=True, help="CSV anterior ao matching")
    parser.add_argument("--output", type=Path, required=True, help="Pasta nova (não pode existir)")
    args = parser.parse_args(argv)
    try:
        run(
            args.input,
            args.output,
            [sys.executable, sys.argv[0], *(argv if argv is not None else sys.argv[1:])],
        )
    except (ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrompido; consulte status incompleto no JSON.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(
            f"Erro ({type(exc).__name__}): confira CSV UTF-8, esquema, permissões e espaço em disco; consulte JSON de status.",
            file=sys.stderr,
        )
        return 1
    print(f"Concluído. Relatórios em: {args.output.resolve()}", flush=True)
    return 0
