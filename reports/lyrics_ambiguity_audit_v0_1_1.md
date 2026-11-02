# Auditoria e recalibração das ambiguidades — v0.1.1

## Escopo e controles

- Processamento integralmente offline a partir dos 100 caches privados existentes.
- Requisições de rede realizadas: **0**.
- Caches das outras 1.900 composições: **0**.
- Coorte de 2.000, Base v0.1.1 e split preservados.
- O fingerprint flexível foi calculado somente para diagnóstico e nunca participou da aceitação.
- Nenhum texto, trecho, token ou n-grama foi incluído nos artefatos públicos.

## Deduplicação observada

- Ocorrências brutas de candidatos: 783.
- Candidatos após deduplicação por ID dentro de cada endpoint: 783.
- Candidatos após união de `/api/get` e `/api/search`: 692.
- Grupos após equivalência estrita de plain: 144.
- Grupos após fingerprint flexível, somente diagnóstico: 137.
- Redução total de ocorrências pela deduplicação/unificação: 91.
- IDs repetidos entre endpoints: 91.
- Composições afetadas por IDs repetidos entre endpoints: 91.
- Buscas que atingiram 20 resultados: 16.

## Antes × depois

| Métrica | Quantidade |
| --- | ---: |
| accepted_exact anterior | 22 |
| accepted_exact_unique | 22 |
| accepted_exact_equivalent | 44 |
| total aceito após recalibração | 66 |
| ambiguous anterior | 72 |
| ambiguous_distinct_lyrics | 28 |
| ambiguous_metadata_conflict | 0 |
| not_found | 6 |
| instrumental | 0 |
| request_error | 0 |
| resolvidos exclusivamente por deduplicação de ID | 0 |
| resolvidos por equivalência estrita de plain | 44 |
| ambiguidades genuínas remanescentes | 28 |

- Cobertura bruta: 94.00%.
- Cobertura automática anterior: 22.00%.
- Cobertura automática recalibrada: 66.00%.

## Causas mutuamente exclusivas nos 72 casos anteriormente ambíguos

| ambiguity_cause | len |
| --- | --- |
| different_ids_same_text_different_metadata | 44 |
| multiple_distinct_plain_lyrics | 28 |

Casos com IDs diferentes e fingerprint estrito igual: 44.
Casos anteriormente ambíguos com mais de um fingerprint estrito de plain: 28.
Destes, casos que colapsariam somente pelo fingerprint flexível, sem autorização para aceite: 4.
Casos equivalentes com diferenças de álbum ou duração: 44.

## Distribuições do status recalibrado

### Período

| period | reclassified_status | len |
| --- | --- | --- |
| 2000-2005 | accepted_exact_equivalent | 10 |
| 2000-2005 | accepted_exact_unique | 2 |
| 2000-2005 | ambiguous_distinct_lyrics | 4 |
| 2006-2011 | accepted_exact_equivalent | 9 |
| 2006-2011 | accepted_exact_unique | 6 |
| 2006-2011 | ambiguous_distinct_lyrics | 4 |
| 2006-2011 | not_found | 2 |
| 2012-2017 | accepted_exact_equivalent | 21 |
| 2012-2017 | accepted_exact_unique | 8 |
| 2012-2017 | ambiguous_distinct_lyrics | 10 |
| 2012-2017 | not_found | 2 |
| 2018-2023 | accepted_exact_equivalent | 4 |
| 2018-2023 | accepted_exact_unique | 6 |
| 2018-2023 | ambiguous_distinct_lyrics | 10 |
| 2018-2023 | not_found | 2 |

### Quintil usado somente na amostragem

| popularity_quintile | reclassified_status | len |
| --- | --- | --- |
| Q1 | accepted_exact_equivalent | 7 |
| Q1 | accepted_exact_unique | 9 |
| Q1 | ambiguous_distinct_lyrics | 2 |
| Q1 | not_found | 3 |
| Q2 | accepted_exact_equivalent | 13 |
| Q2 | accepted_exact_unique | 2 |
| Q2 | ambiguous_distinct_lyrics | 5 |
| Q3 | accepted_exact_equivalent | 11 |
| Q3 | accepted_exact_unique | 6 |
| Q3 | ambiguous_distinct_lyrics | 3 |
| Q3 | not_found | 1 |
| Q4 | accepted_exact_equivalent | 6 |
| Q4 | accepted_exact_unique | 3 |
| Q4 | ambiguous_distinct_lyrics | 8 |
| Q4 | not_found | 2 |
| Q5 | accepted_exact_equivalent | 7 |
| Q5 | accepted_exact_unique | 2 |
| Q5 | ambiguous_distinct_lyrics | 10 |

### Gênero

| genre | reclassified_status | len |
| --- | --- | --- |
| acoustic | accepted_exact_equivalent | 3 |
| alt-rock | accepted_exact_equivalent | 6 |
| alt-rock | ambiguous_distinct_lyrics | 6 |
| black-metal | accepted_exact_equivalent | 2 |
| black-metal | accepted_exact_unique | 3 |
| blues | accepted_exact_equivalent | 1 |
| blues | accepted_exact_unique | 1 |
| chill | ambiguous_distinct_lyrics | 1 |
| country | accepted_exact_equivalent | 2 |
| country | accepted_exact_unique | 3 |
| country | ambiguous_distinct_lyrics | 6 |
| dance | accepted_exact_equivalent | 2 |
| dance | ambiguous_distinct_lyrics | 2 |
| dance | not_found | 1 |
| death-metal | accepted_exact_equivalent | 4 |
| death-metal | accepted_exact_unique | 3 |
| death-metal | ambiguous_distinct_lyrics | 2 |
| death-metal | not_found | 1 |
| disco | ambiguous_distinct_lyrics | 1 |
| electro | accepted_exact_unique | 1 |
| emo | accepted_exact_equivalent | 4 |
| emo | accepted_exact_unique | 4 |
| emo | ambiguous_distinct_lyrics | 2 |
| folk | accepted_exact_equivalent | 3 |
| folk | ambiguous_distinct_lyrics | 2 |
| garage | accepted_exact_equivalent | 2 |
| garage | accepted_exact_unique | 3 |
| garage | ambiguous_distinct_lyrics | 1 |
| goth | accepted_exact_equivalent | 1 |
| grindcore | accepted_exact_unique | 1 |
| hard-rock | accepted_exact_equivalent | 2 |
| hardcore | accepted_exact_equivalent | 4 |
| hardcore | accepted_exact_unique | 1 |
| hardcore | ambiguous_distinct_lyrics | 2 |
| hardcore | not_found | 1 |
| hip-hop | accepted_exact_equivalent | 2 |
| hip-hop | ambiguous_distinct_lyrics | 1 |
| indie-pop | accepted_exact_equivalent | 3 |
| indie-pop | ambiguous_distinct_lyrics | 1 |
| industrial | accepted_exact_unique | 1 |
| metal | accepted_exact_equivalent | 1 |
| metalcore | ambiguous_distinct_lyrics | 1 |
| power-pop | accepted_exact_equivalent | 2 |
| power-pop | not_found | 2 |
| ska | not_found | 1 |
| soul | accepted_exact_unique | 1 |

### Método do match Spotify–LFM2b

| match_method | reclassified_status | len |
| --- | --- | --- |
| raw_exact | accepted_exact_equivalent | 43 |
| raw_exact | accepted_exact_unique | 22 |
| raw_exact | ambiguous_distinct_lyrics | 27 |
| raw_exact | not_found | 6 |
| strict_normalized | accepted_exact_equivalent | 1 |
| strict_normalized | ambiguous_distinct_lyrics | 1 |

### Disponibilidade de plain

| any_plain_lyrics_available | reclassified_status | len |
| --- | --- | --- |
| False | not_found | 6 |
| True | accepted_exact_equivalent | 44 |
| True | accepted_exact_unique | 22 |
| True | ambiguous_distinct_lyrics | 28 |

### Disponibilidade de synced

| any_synced_lyrics_available | reclassified_status | len |
| --- | --- | --- |
| False | accepted_exact_equivalent | 3 |
| False | accepted_exact_unique | 10 |
| False | not_found | 6 |
| True | accepted_exact_equivalent | 41 |
| True | accepted_exact_unique | 12 |
| True | ambiguous_distinct_lyrics | 28 |

## Interpretação e recomendação

A recalibração aceita somente um candidato exato único com plain disponível ou um conjunto de candidatos exatos cujos fingerprints estritos de plain sejam todos idênticos. Duração, endpoint, completude e ID servem apenas para escolher um representante dentro de um conjunto já comprovadamente equivalente; não transformam candidatos com textos distintos em aceitos.

**Recomendação: realizar um pequeno teste complementar.** A cobertura automática subiu para 66% sem erro técnico, mas 28 casos ainda contêm letras estritamente distintas e o smoke original não cobriu adequadamente métodos de matching e versões. Um teste complementar pequeno e estratificado deve preceder qualquer escala; as outras 1.900 composições não devem ser consultadas nesta versão.
