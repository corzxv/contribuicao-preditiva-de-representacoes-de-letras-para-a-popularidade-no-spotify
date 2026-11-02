"""02 — Consulta somente pendências LRCLIB; --retry-errors trata falhas transitórias."""

from tcc_music_popularity.manual_lyrics import cli

if __name__ == "__main__":
    raise SystemExit(cli(2))
