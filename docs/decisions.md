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

## D-007 — Base v0.1.1 e holdout agrupado

A Base v0.1.1 mantém as 111.758 observações aceitas, mas reduz a matriz de 310 para 228 colunas: três identificadores, três grupos operacionais, o rótulo do split, o alvo e 220 preditoras autorizadas. O split é determinístico (`random_state=42`), aproximadamente 75/25 e feito sobre componentes conexos de artista e composição. Assim, uma composição que ligue registros ou artistas permanece integralmente no mesmo subconjunto. Não houve sobreposição de `artist_group_id`, `composition_group_id` nem `split_group_id`.

As 12 preditoras constantes foram identificadas exclusivamente no desenvolvimento e removidas da matriz. As 42.517 linhas com ausências em descritores estruturais foram preservadas; não se imputou zero. `genius_lyrics_views`, `lfm_playcount`, chaves, nomes e artefatos de matching são proibidos como preditores. O holdout não deve ser usado para seleção de variáveis, PCA ou ajuste de hiperparâmetros.

## D-008 — Escopo da revisão de matching

O status aceito continua sendo a regra da Base v0.1; divergências temporais não são convertidas automaticamente em erro. A amostra manual contém 225 casos, reaproveita 222 registros do artefato existente e faz três reposições determinísticas para cobrir chave de composição ausente e flags raras de versão. Os cinco campos humanos são entregues em branco.
