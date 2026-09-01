# Proveniência

## Spotify_1Million_Tracks

- Página: https://www.kaggle.com/datasets/amitanshjoshi/spotify-1million-tracks
- Slug: `amitanshjoshi/spotify-1million-tracks`
- Arquivo observado: `spotify_data.csv`
- Tamanho: 175.822.041 bytes
- SHA-256: `42fff9e85d1b26c3653b4668959d1be395fab8956848f0478bf28f726b3d5897`
- Aquisição: API pública Kaggle, ZIP `spotify-1million-tracks.zip`, em 2026-08-18 UTC
- Licença observada na API/página oficial: “Database: Open Database, Contents: © Original Authors”
- Última atualização informada pela API: 2023-06-21T12:27:55.677Z

## LFM2b Lyrics Descriptor Analyses

- Registro: https://zenodo.org/records/10938615
- DOI: `10.5281/zenodo.10938615`
- Arquivo: `full_dataset.json.gz`
- Tamanho: 690.455.174 bytes
- SHA-256: `0a7c3d52584c4f726fb4e06e62ce36f00ff1b428811561409e6941df8428d106`
- MD5 publicado pelo Zenodo: `9c2aab67c8228a6238a7c2c030d6bef1`
- Aquisição: link de conteúdo oficial Zenodo em 2026-08-18 UTC
- Licença confirmada pela API Zenodo: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

O registro oficial descreve `popularity` como visualizações da letra no Genius e `lfm_playcount` como eventos de escuta LFM-2b. O arquivo oferece descritores derivados das letras; esta pipeline não afirma que contenha letra integral.

O manifesto legível por máquina fica em `data/raw/manifest.json` e não é versionado porque pertence à camada de dados local.

## Derivados locais — Base v0.1.1

- Fonte imutável: `data/processed/modeling_base_lfm_v0_1.parquet`
- SHA-256 da fonte antes e depois da execução: `7a0c15c905081fb7fe672478513d706c40fbd709d2af4077173803484a02ab59`
- `data/processed/modeling_base_lfm_v0_1_1.parquet`: 69.544.162 bytes; SHA-256 `1c28f31e9b466b76d7e0180b769ba7ac51c46d2590ad7b1ba1ed21eaebdd1c5c`
- `data/processed/split_assignments_v0_1_1.parquet`: 11.322.914 bytes; SHA-256 `4b0ff5a0e9be21af15607b9bbced423c99247c7d1aaa9615635baf134b86856b`
- `data/processed/matching_audit_v0_1_1.parquet`: 14.614.968 bytes; SHA-256 `3b7b9a2145b91ce7c47ac85ef61c17784b7a371633e494b6bac34fb85b54c346`
- `reports/feature_manifest_v0_1_1.csv`: 159.893 bytes; SHA-256 `f2dd09defb9bbe383e3c189b65f836a5ba4906e090b472e2604cba388a243d42`
- `reports/match_review_sample_v0_1_1.xlsx`: 77.540 bytes; SHA-256 `d7cef88b58cb9c0707f04146b88307bacfc8c1395786f3e7fd2400bd7f039953`

Os Parquets v0.1.1 e demais derivados volumosos continuam ignorados pelo Git conforme as regras do projeto. A configuração executável está em `configs/modeling_v0_1_1.yaml`; o resumo de execução e os detalhes de ambiente estão em `reports/run_summary_v0_1_1.json`.
