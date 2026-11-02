# Validação da Base v0.1.1

Gerado em `2026-09-01T00:10:37.202464+00:00` a partir de `data/processed/modeling_base_lfm_v0_1.parquet`.

## Escopo e interpretação

`spotify_popularity` é popularidade histórica presente no snapshot da fonte. Não representa sucesso futuro, causalidade nem probabilidade de uma faixa tornar-se hit. A população inferencial permanece o subconjunto Spotify associado com alta confiança ao LFM2b.

## Consistência entre artefatos

| fonte | métrica | documentado | observado | consistente |
| --- | --- | --- | --- | --- |
| Parquet v0.1 | base rows | 111758 | 111758 | sim |
| run_summary.json | accepted matches | 111758 | 111758 | sim |
| matching_report.md / matching_summary.json | accepted matches | 111758 | 111758 | sim |
| base_preview.xlsx | rows / columns / descriptors | {"rows": 111758, "columns": 310, "descriptors": 209} | {"rows": 111758, "columns": 310, "descriptors": 209} | sim |
| data_audit.md / spotify_audit.json | Spotify rows | 1159764 | 1159764 | sim |
| data_audit.md / lfm2b_audit.json | LFM rows / columns / descriptors | {"rows": 582759, "columns": 242, "descriptors": 209} | {"rows": 582759, "columns": 242, "descriptors": 209} | sim |

Inconsistências de contagens centrais: **0**.

## Perfil observado da Base v0.1

- Linhas: **111,758**.
- Colunas: **310**.
- `track_id` únicos: **111,758**.
- `spotify_row_id` únicos: **111,758**.
- `lfm_record_key` únicos: **111,758**.
- Células ausentes: **870,004**.
- Valores infinitos: **0**.
- Colunas constantes na base completa: **32**.
- Colunas com variância próxima de zero: **0**.

A regra operacional de variância próxima de zero para colunas numéricas não constantes foi `variância <= 1e-12 × max(1, média²)`; o cálculo de cardinalidade e constantes considerou valores não ausentes.

## Resolução 231 versus 209

O inventário preliminar `lfm2b_schema_inventory.json` listou 231 supostos descritores por uma regra inclusiva. A auditoria semântica posterior confirmou **209 descritores de letra**. Os **22 campos excedentes** são normalizações, flags de versão e chaves técnicas; não são descritores líricos. No schema integrado há 242 colunas de origem LFM2b: 209 descritores e 33 campos de metadados, identificação, popularidade externa, normalização, versão ou qualidade.

Campos excedentes do inventário preliminar:

`lfm_acoustic`, `lfm_artist_collaborators_json`, `lfm_artist_conservative`, `lfm_artist_primary`, `lfm_artist_strict`, `lfm_artist_unicode`, `lfm_composition_key`, `lfm_demo`, `lfm_instrumental`, `lfm_live`, `lfm_mono_stereo`, `lfm_normalization_version`, `lfm_radio_edit`, `lfm_release_date_numberlong`, `lfm_remaster`, `lfm_remix`, `lfm_title_base`, `lfm_title_conservative`, `lfm_title_strict`, `lfm_title_unicode`, `lfm_version_tags`, `lfm_year_mentioned`.

## Saneamento e matriz controlada

- Base v0.1 original: **111,758 × 310**; não alterada.
- Base v0.1.1: **111,758 × 228**.
- Linhas excluídas: **0**.
- Preditoras candidatas antes da remoção de constantes: **232**.
- Preditoras/controles autorizados após remoção: **220**.
- Variáveis constantes removidas da matriz: **12**.

Variáveis constantes removidas: `lfm_affective_liwc_numerals`, `lfm_affective_nrcaffectintensity_anticipation`, `lfm_affective_nrcaffectintensity_disgust`, `lfm_affective_nrcaffectintensity_negative`, `lfm_affective_nrcaffectintensity_positive`, `lfm_affective_nrcaffectintensity_surprise`, `lfm_affective_nrcaffectintensity_trust`, `lfm_affective_nrchashtagemotion_negative`, `lfm_affective_nrchashtagemotion_positive`, `lfm_structure_ends_with_two_chorus_repetitions`, `lfm_structure_pattern_two_choruses_at_least_one_verse`, `lfm_uncommon_words_ratio`.

## Ausências

Ausências estruturais não foram convertidas em zero. O bloco estrutural da letra possui 42,517 linhas com ausência em pelo menos um campo. A estratégia futura é: indicador de ausência, imputação ajustada somente em `development_train`, análise de sensibilidade e avaliação de bloco estrutural separado. Nenhuma imputação, média, escala ou transformação foi aprendida nesta etapa.

## Artefatos de rastreabilidade

As variáveis de matching, métricas externas, nomes, títulos, chaves e flags de auditoria ficaram fora da matriz de modelagem e permanecem em `matching_audit_v0_1_1.parquet` e no manifesto.
