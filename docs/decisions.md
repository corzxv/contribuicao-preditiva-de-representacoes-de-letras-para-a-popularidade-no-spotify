# Decisões técnicas e científicas

## D-001 — Parquet + DuckDB

Polars processa Spotify e lotes LFM2b; Parquet Zstandard é a camada persistente; DuckDB cataloga views. Alternativa rejeitada nesta versão: banco servidor, por aumentar operação sem necessidade.

## D-002 — Popularidades separadas

`spotify_popularity`, `genius_lyrics_views` e `lfm_playcount` nunca são fundidas. A primeira é snapshot Spotify; a segunda são visualizações de letra no Genius; a terceira é contagem de escutas LFM-2b.

## D-003 — Matching conservador

Somente artista+título, nunca título isolado. Pares normalizados precisam ser únicos e compatíveis em versões. Ambiguidades são preservadas. Fuzzy gera fila de revisão, não decisão.

## D-004 — Datas MongoDB heterogêneas

O schema real contém 573.829 datas ISO e 8.930 epochs negativos em `$numberLong`. Ambos permanecem; `lfm_release_year` é derivado. Anos <1850 recebem flag, sem exclusão.

## D-005 — Gêneros Spotify

Os 82 gêneros têm contagens bastante variáveis; não foi observado balanceamento por contagem exatamente igual. Isso não comprova representatividade: a fonte informa extração via Spotipy, mas o mecanismo de seleção de faixas/gêneros não permite inferir uma amostra probabilística de todo o Spotify.

## D-006 — Sem modelos na Base v0.1

Não há treinamento, embeddings nem redes neurais. Na modelagem futura, splits devem ser agrupados por artista e composição para reduzir leakage entre versões relacionadas.

