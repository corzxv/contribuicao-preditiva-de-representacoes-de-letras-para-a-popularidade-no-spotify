# Relatório de matching — Spotify × LFM2b

Gerado em: `2026-08-18T01:53:01.770576+00:00`.

## Funil por método e status

| method | status | candidate_rows | spotify_tracks | percent_of_spotify_tracks |
| --- | --- | --- | --- | --- |
| base_title_version_compatible | accepted_with_rules | 3308 | 3308 | 0.28523 |
| base_title_version_compatible | ambiguous | 8062 | 5755 | 0.496222 |
| conservative_normalized | accepted_with_rules | 9032 | 9032 | 0.778779 |
| conservative_normalized | ambiguous | 1531 | 1442 | 0.124336 |
| fuzzy_candidate | candidate_for_review | 3457 | 3024 | 0.260743 |
| raw_exact | accepted_high_confidence | 79740 | 79740 | 6.875537 |
| raw_exact | ambiguous | 1688 | 1688 | 0.145547 |
| strict_normalized | accepted_high_confidence | 19678 | 19678 | 1.696725 |
| strict_normalized | ambiguous | 854 | 848 | 0.073118 |

## Multiplicidades determinísticas

| mapping_type | candidate_rows | spotify_tracks | lfm_records |
| --- | --- | --- | --- |
| many_spotify_to_one_lfm | 5509 | 5509 | 1916 |
| many_to_many | 4183 | 1563 | 1167 |
| one_spotify_to_many_lfm | 2443 | 1121 | 2443 |
| one_to_one | 111758 | 111758 | 111758 |

A amostra estratificada para revisão permanece pendente em `data/processed/spotify_lfm_review_sample.parquet`.

Matches fuzzy permanecem `candidate_for_review`; nenhum foi aceito automaticamente. Mapeamentos não únicos permanecem ambíguos e não entram na base analítica.

## Diagnóstico de seleção

Cobertura aceita: **111,758 / 1,159,764 (9.6363%)**.

Popularidade Spotify média — matched: 27.1641; unmatched: 17.4467.

Popularidade Spotify mediana — matched: 26.0000; unmatched: 14.0000.

> O subconjunto encontrado não deve ser tratado como aleatório ou representativo. As diferenças descrevem cobertura do cruzamento e não sustentam explicação nem causalidade.

## Riscos e uso futuro

Os principais riscos são colisões de nomes normalizados, versões incompatíveis, múltiplas gravações da mesma composição e diferenças temporais. Apenas pares únicos aceitos entram em `modeling_base_lfm_v0_1`; a granularidade é um par Spotify–LFM2b aceito, não uma composição universal.

A comparação de cobertura não permite concluir que descritores de letras expliquem popularidade.

## Figuras

- [Funil de matching](figures/matching_funnel.png)
- [Taxa de match por ano](figures/match_rate_by_year.png)
- [Taxa de match por gênero](figures/match_rate_by_genre.png)
- [Popularidade matched × unmatched](figures/popularity_matched_unmatched.png)
- [Distribuição temporal matched × não aceito](figures/temporal_matched_unmatched.png)