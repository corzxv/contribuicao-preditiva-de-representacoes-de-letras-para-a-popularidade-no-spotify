# TCC popularidade musical, Base v0.1.1

Pipeline Python reproduzível para avaliar, em etapas futuras, a contribuição preditiva incremental de descritores de letras na estimação da popularidade Spotify observada. O projeto trata associação e predição; não faz afirmações causais e não treina modelos nesta versão.

## Resultados observados nesta execução

- Spotify: 1.159.764 registros, 1.159.764 `track_id` únicos, anos 2000–2023.
- LFM2b: 582.759 registros válidos e 209 descritores identificados; 0 JSON inválido.
- Matching aceito: 111.758 faixas Spotify (9,6363%).
- Ambíguas: 8.178 faixas Spotify / 12.135 pares candidatos.
- Fuzzy pendente: 3.024 faixas / 3.457 pares; nenhum aceito automaticamente.
- Base analítica: 111.758 pares aceitos, sem letra bruta.

Esses números pertencem aos arquivos com hashes registrados em [docs/provenance.md](docs/provenance.md). `spotify_popularity` é um snapshot da fonte e não mede necessariamente popularidade no lançamento ou sucesso futuro.

## Instalação

Requer Python 3.11–3.13. `uv` não estava disponível nesta execução; foi usado `venv` + `pip`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
```

As fontes públicas são reutilizadas quando já existem. Dados, DuckDB, credenciais e caches são ignorados pelo Git.

## Comandos

```powershell
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli acquire
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli audit
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli normalize
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli match
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli report
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli all
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli prepare-v011
```

Comando único de reprodução:

```powershell
.\.venv\Scripts\python.exe -m tcc_music_popularity.cli all
```

## Fontes

- [Spotify_1Million_Tracks — Kaggle](https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks)
- [LFM2b Lyrics Descriptor Analyses — Zenodo](https://zenodo.org/records/10938615)

O LFM2b fornece descritores derivados das letras, não é tratado aqui como corpus de letras integrais. Seu campo original `popularity` é renomeado para `genius_lyrics_views`; `lfm_playcount` e `spotify_popularity` permanecem separados.

## Produtos principais

- `data/processed/spotify_tracks.parquet`: uma linha por registro Spotify.
- `data/processed/lfm2b_tracks.parquet`: uma linha por registro LFM2b.
- `data/processed/spotify_lfm_matches.parquet`: pares aceitos.
- `data/processed/modeling_base_lfm_v0_1.parquet`: uma linha por par aceito.
- `data/processed/modeling_base_lfm_v0_1_1.parquet`: matriz preparada, com split e somente variáveis autorizadas.
- `data/processed/split_assignments_v0_1_1.parquet`: atribuição reprodutível desenvolvimento/holdout, agrupada por artista e composição.
- `data/processed/matching_audit_v0_1_1.parquet`: auditoria temporal, de identidade, versões e matching.
- [reports/feature_manifest_v0_1_1.csv](reports/feature_manifest_v0_1_1.csv): papel, elegibilidade, ausências e risco de leakage de cada campo.
- [reports/match_review_sample_v0_1_1.xlsx](reports/match_review_sample_v0_1_1.xlsx): amostra de 225 pares para rotulagem humana.
- `data/processed/music_tcc.duckdb`: views e catálogo das camadas Parquet.
- [reports/data_audit.md](reports/data_audit.md) e [reports/matching_report.md](reports/matching_report.md).

`prepare-v011` não treina modelos. Ele valida a Base v0.1, remove do conjunto de preditores apenas constantes identificadas no desenvolvimento, preserva ausências estruturais e cria um holdout intocado de aproximadamente 25% sem sobreposição de artista ou composição.

## Qualidade e desenvolvimento

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

A lógica fica em `src/tcc_music_popularity`; notebooks futuros não devem ser a única fonte de transformações.
