# Amostragem do Piloto de Letras v0.1

## Resultado

- Seed: `20260901`.
- Universo: somente `development_train` da Base v0.1.1 revisada.
- Linhas no desenvolvimento: 83,817.
- Linhas excluídas por `composition_key` ausente: 8.
- Composições elegíveis únicas: 83,559.
- Linhas redundantes colapsadas na escolha de representante: 250.
- Coorte selecionada: 2,000 composições únicas.
- Smoke test pré-selecionado: 100 composições únicas.
- Limiares dos quintis de `spotify_popularity`, calculados somente em `development_train`: 14.0, 22.0, 30.0, 39.0.

## Regra do representante

Para cada `composition_key`, sem usar popularidade no ranqueamento: (1) preferência por registros sem flags live/remix/acoustic/karaoke; (2) maior confiança do match Spotify–LFM2b por status, método e score já congelados; (3) maior completude de artista, título e duração; (4) menor `spotify_row_id`, seguido do menor `track_id`, como desempate estável.

## Alocação

A alocação primária é proporcional nos 20 estratos período × quintil. Dentro de cada estrato, a alocação proporcional conjunta usa gênero, método de matching e perfil de versão. Restos e déficits são redistribuídos pelo método de Hamilton com desempate lexical determinístico. A seleção dentro das células usa SHA-256 com a seed informada. O mesmo princípio gera o smoke de 100 casos a partir da coorte de 2.000.

### Universo elegível por estrato primário

| period | popularity_quintile | n |
| --- | --- | --- |
| 2000-2005 | Q1 | 4491 |
| 2000-2005 | Q2 | 3431 |
| 2000-2005 | Q3 | 2778 |
| 2000-2005 | Q4 | 1707 |
| 2000-2005 | Q5 | 1020 |
| 2006-2011 | Q1 | 4871 |
| 2006-2011 | Q2 | 4491 |
| 2006-2011 | Q3 | 3703 |
| 2006-2011 | Q4 | 2379 |
| 2006-2011 | Q5 | 1593 |
| 2012-2017 | Q1 | 5446 |
| 2012-2017 | Q2 | 6977 |
| 2012-2017 | Q3 | 7450 |
| 2012-2017 | Q4 | 7139 |
| 2012-2017 | Q5 | 6904 |
| 2018-2023 | Q1 | 2004 |
| 2018-2023 | Q2 | 2595 |
| 2018-2023 | Q3 | 3425 |
| 2018-2023 | Q4 | 4505 |
| 2018-2023 | Q5 | 6650 |

### Coorte de 2.000 por estrato primário

| period | popularity_quintile | n |
| --- | --- | --- |
| 2000-2005 | Q1 | 108 |
| 2000-2005 | Q2 | 82 |
| 2000-2005 | Q3 | 66 |
| 2000-2005 | Q4 | 41 |
| 2000-2005 | Q5 | 24 |
| 2006-2011 | Q1 | 117 |
| 2006-2011 | Q2 | 108 |
| 2006-2011 | Q3 | 89 |
| 2006-2011 | Q4 | 57 |
| 2006-2011 | Q5 | 38 |
| 2012-2017 | Q1 | 130 |
| 2012-2017 | Q2 | 167 |
| 2012-2017 | Q3 | 178 |
| 2012-2017 | Q4 | 171 |
| 2012-2017 | Q5 | 165 |
| 2018-2023 | Q1 | 48 |
| 2018-2023 | Q2 | 62 |
| 2018-2023 | Q3 | 82 |
| 2018-2023 | Q4 | 108 |
| 2018-2023 | Q5 | 159 |

### Smoke de 100 por estrato primário

| period | popularity_quintile | n |
| --- | --- | --- |
| 2000-2005 | Q1 | 6 |
| 2000-2005 | Q2 | 4 |
| 2000-2005 | Q3 | 3 |
| 2000-2005 | Q4 | 2 |
| 2000-2005 | Q5 | 1 |
| 2006-2011 | Q1 | 6 |
| 2006-2011 | Q2 | 5 |
| 2006-2011 | Q3 | 5 |
| 2006-2011 | Q4 | 3 |
| 2006-2011 | Q5 | 2 |
| 2012-2017 | Q1 | 7 |
| 2012-2017 | Q2 | 8 |
| 2012-2017 | Q3 | 9 |
| 2012-2017 | Q4 | 9 |
| 2012-2017 | Q5 | 8 |
| 2018-2023 | Q1 | 2 |
| 2018-2023 | Q2 | 3 |
| 2018-2023 | Q3 | 4 |
| 2018-2023 | Q4 | 5 |
| 2018-2023 | Q5 | 8 |

## Controles

- Nenhum registro do `holdout_test` foi utilizado.
- Casos sem `composition_key` não foram selecionados.
- O lookup de consulta não contém `spotify_popularity`, `genius_lyrics_views`, `lfm_playcount` nem qualquer quintil ou métrica de sucesso.
- A fonte não fornece álbum no schema congelado utilizado; `album_name_query` permanece nulo e não é inventado.
- A seleção busca cobertura e heterogeneidade; não pretende maximizar taxa de sucesso da coleta.
