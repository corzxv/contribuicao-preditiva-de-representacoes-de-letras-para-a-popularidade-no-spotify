"""Normalização conservadora e não destrutiva de artista e título."""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

import polars as pl

NORMALIZATION_VERSION = "v0.1.0"

_FEAT_RE = re.compile(r"\s+(?:feat(?:uring)?\.?|ft\.?)\s+", re.IGNORECASE)
_SMART_PUNCTUATION = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})
_VERSION_PATTERNS: dict[str, re.Pattern[str]] = {
    "remaster": re.compile(r"\b(?:\d{4}\s+)?remaster(?:ed)?\b", re.IGNORECASE),
    "remix": re.compile(r"\b(?:remix|mix)\b", re.IGNORECASE),
    "live": re.compile(r"\blive\b", re.IGNORECASE),
    "acoustic": re.compile(r"\bacoustic(?:\s+version)?\b", re.IGNORECASE),
    "radio_edit": re.compile(r"\bradio\s+edit\b", re.IGNORECASE),
    "mono_stereo": re.compile(r"\b(?:mono|stereo)(?:\s+version|\s+mix)?\b", re.IGNORECASE),
    "instrumental": re.compile(r"\binstrumental\b", re.IGNORECASE),
    "demo": re.compile(r"\bdemo\b", re.IGNORECASE),
}
_BRACKETED_RE = re.compile(r"\s*[\[(]([^\])]+)[\])]\s*")
_DASH_SUFFIX_RE = re.compile(r"\s+-\s+(.+)$")
_YEAR_RE = re.compile(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)")


def unicode_normalize(value: Any) -> str | None:
    if value is None:
        return None
    return unicodedata.normalize("NFC", str(value).translate(_SMART_PUNCTUATION))


def normalize_spaces(value: Any) -> str | None:
    normalized = unicode_normalize(value)
    return re.sub(r"\s+", " ", normalized).strip() if normalized is not None else None


def strict_normalize(value: Any) -> str | None:
    spaced = normalize_spaces(value)
    return spaced.casefold() if spaced is not None else None


def remove_diacritics(value: Any) -> str | None:
    normalized = unicode_normalize(value)
    if normalized is None:
        return None
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(character)
    )


def conservative_normalize(value: Any) -> str | None:
    normalized = remove_diacritics(value)
    if normalized is None:
        return None
    normalized = normalized.casefold().replace("&", " and ").replace("/", "")
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return re.sub(r"\s+", " ", normalized).strip()


def split_artist(value: Any) -> tuple[str | None, list[str]]:
    spaced = normalize_spaces(value)
    if not spaced:
        return spaced, []
    parts = _FEAT_RE.split(spaced, maxsplit=1)
    if len(parts) == 1:
        return parts[0], []
    collaborators = [
        piece.strip() for piece in re.split(r"\s*(?:,|&|\band\b)\s*", parts[1]) if piece.strip()
    ]
    return parts[0].strip(), collaborators


def classify_version(value: Any) -> dict[str, Any]:
    spaced = normalize_spaces(value) or ""
    tags = {name: bool(pattern.search(spaced)) for name, pattern in _VERSION_PATTERNS.items()}
    years = [int(year) for year in _YEAR_RE.findall(spaced)]
    tags["year_mentioned"] = years[-1] if years else None
    tags["version_tags"] = sorted(name for name, present in tags.items() if present is True)
    return tags


def base_title(value: Any) -> str | None:
    spaced = normalize_spaces(value)
    if spaced is None:
        return None

    def bracket_replacer(match: re.Match[str]) -> str:
        content = match.group(1)
        return (
            " "
            if any(pattern.search(content) for pattern in _VERSION_PATTERNS.values())
            else match.group(0)
        )

    result = _BRACKETED_RE.sub(bracket_replacer, spaced)
    suffix = _DASH_SUFFIX_RE.search(result)
    if suffix and any(pattern.search(suffix.group(1)) for pattern in _VERSION_PATTERNS.values()):
        result = result[: suffix.start()]
    return normalize_spaces(result)


def composition_key(artist: Any, title: Any) -> str | None:
    primary, _ = split_artist(artist)
    left = conservative_normalize(primary)
    right = conservative_normalize(base_title(title))
    return f"{left}|||{right}" if left and right else None


def _normalized_pair(artist: Any, title: Any) -> dict[str, Any]:
    primary, collaborators = split_artist(artist)
    title_base = base_title(title)
    version = classify_version(title)
    artist_key = conservative_normalize(primary)
    title_key = conservative_normalize(title_base)
    return {
        "artist_unicode": unicode_normalize(artist),
        "artist_strict": strict_normalize(artist),
        "artist_conservative": conservative_normalize(artist),
        "artist_primary": primary,
        "artist_collaborators_json": json.dumps(collaborators, ensure_ascii=False),
        "title_unicode": unicode_normalize(title),
        "title_strict": strict_normalize(title),
        "title_conservative": conservative_normalize(title),
        "title_base": title_base,
        **version,
        "composition_key": f"{artist_key}|||{title_key}" if artist_key and title_key else None,
        "normalization_version": NORMALIZATION_VERSION,
    }


def add_normalized_columns(
    frame: pl.DataFrame, artist_col: str, title_col: str, prefix: str = ""
) -> pl.DataFrame:
    """Adiciona variantes sem sobrescrever as colunas informadas."""
    p = f"{prefix}_" if prefix else ""
    normalized_struct = pl.struct([artist_col, title_col]).map_elements(
        lambda row: _normalized_pair(row[artist_col], row[title_col]),
        return_dtype=pl.Struct(
            [
                pl.Field("artist_unicode", pl.String),
                pl.Field("artist_strict", pl.String),
                pl.Field("artist_conservative", pl.String),
                pl.Field("artist_primary", pl.String),
                pl.Field("artist_collaborators_json", pl.String),
                pl.Field("title_unicode", pl.String),
                pl.Field("title_strict", pl.String),
                pl.Field("title_conservative", pl.String),
                pl.Field("title_base", pl.String),
                pl.Field("remaster", pl.Boolean),
                pl.Field("remix", pl.Boolean),
                pl.Field("live", pl.Boolean),
                pl.Field("acoustic", pl.Boolean),
                pl.Field("radio_edit", pl.Boolean),
                pl.Field("mono_stereo", pl.Boolean),
                pl.Field("instrumental", pl.Boolean),
                pl.Field("demo", pl.Boolean),
                pl.Field("year_mentioned", pl.Int64),
                pl.Field("version_tags", pl.List(pl.String)),
                pl.Field("composition_key", pl.String),
                pl.Field("normalization_version", pl.String),
            ]
        ),
    )
    result = frame.with_columns(normalized_struct.alias("_normalized")).unnest("_normalized")
    normalized_names = [
        "artist_unicode",
        "artist_strict",
        "artist_conservative",
        "artist_primary",
        "artist_collaborators_json",
        "title_unicode",
        "title_strict",
        "title_conservative",
        "title_base",
        *_VERSION_PATTERNS,
        "year_mentioned",
        "version_tags",
        "composition_key",
        "normalization_version",
    ]
    return result.rename({name: f"{p}{name}" for name in normalized_names})
