# Auditoria de matching e temporal — Base v0.1.1

Gerado em `2026-09-01T00:10:37.202464+00:00`. Todos os **111,758** pares aceitos da Base v0.1 foram auditados.

## Distribuições do matching

### Método

| match_method | n | % |
| --- | --- | --- |
| raw_exact | 79740 | 71.350597% |
| strict_normalized | 19678 | 17.607688% |
| conservative_normalized | 9032 | 8.081748% |
| base_title_version_compatible | 3308 | 2.959967% |

### Status e justificativa

| match_status | n |
| --- | --- |
| accepted_high_confidence | 99418 |
| accepted_with_rules | 12340 |

| acceptance_reason | n |
| --- | --- |
| unique_exact_or_strict_pair | 99418 |
| unique_conservative_pair_with_compatible_version | 12340 |

`match_score` não se aplica aos pares determinísticos aceitos: valores não ausentes = **0**. `version_compatible=True` em **111,758** pares. `temporal_compatible=True` em **99,784** e `False` em **11,974**.

## Diferença temporal absoluta

- Média: **2.092718** anos.
- Mediana: **0.000000**.
- Desvio-padrão: **20.626956**.
- Mínimo/máximo: **0 / 2018**.
- Quantis: `{"0.01": 0.0, "0.05": 0.0, "0.25": 0.0, "0.5": 0.0, "0.75": 0.0, "0.95": 13.0, "0.99": 38.0}`.

| faixa | n | % |
| --- | --- | --- |
| diferença 0 | 90094 | 80.615258% |
| 1–2 anos | 9690 | 8.670520% |
| 3–5 anos | 2605 | 2.330929% |
| 6–10 anos | 2624 | 2.347930% |
| 11–20 anos | 3128 | 2.798905% |
| mais de 20 anos | 3617 | 3.236457% |

Diferença temporal não foi tratada automaticamente como erro: uma faixa Spotify recente pode ser relançamento de composição antiga. Há **16** pares com flag de ano LFM implausível; permanecem preservados para revisão.

## Versões

As categorias abaixo não são mutuamente exclusivas, exceto “original/no version flag”. Como todos os pares aceitos são compatíveis em versão, as contagens Spotify e LFM coincidem.

| tipo | n | % |
| --- | --- | --- |
| original_no_version_flag | 105638 | 94.523882% |
| remaster | 571 | 0.510925% |
| remix | 1843 | 1.649099% |
| live | 2624 | 2.347930% |
| acoustic | 460 | 0.411604% |
| radio_edit | 191 | 0.170905% |
| mono_stereo | 69 | 0.061741% |
| instrumental | 177 | 0.158378% |
| demo | 295 | 0.263963% |

## Identidade e multiplicidade

| métrica | valor |
| --- | --- |
| track_id_duplicate_excess_rows | 0 |
| spotify_row_id_duplicate_excess_rows | 0 |
| lfm_record_key_duplicate_excess_rows | 0 |
| composition_keys_with_multiple_rows | 309 |
| rows_in_duplicated_composition_groups | 623 |
| composition_keys_with_multiple_track_ids | 309 |
| maximum_tracks_per_composition_key | 3 |
| tracks_linked_to_multiple_lfm_records | 0 |
| accepted_without_spotify_composition_key | 22 |
| accepted_without_lfm_composition_key | 22 |

Confirmam-se **22** casos aceitos sem `composition_key`. Eles não foram excluídos; receberam grupo de composição por fallback rastreável no split.

## Revisão humana

A amostra v0.1 existente de 225 linhas foi reutilizada. Foram preservadas 222 linhas e feitas 3 substituições determinísticas para incluir chave ausente e tipos de versão faltantes. Os cinco campos humanos permanecem integralmente vazios. A amostra inclui aceitos, ambíguos e candidatos fuzzy; estes últimos continuam sem aceitação automática.
