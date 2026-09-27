# Relatório do Smoke Test — Piloto de Letras v0.1

## Execução observada

- Consultas únicas previstas e processadas: 100.
- Tempo total: 204.862 segundos.
- Cache preexistente na aquisição original: 0.
- Resultados reprocessados do cache nesta execução: 100.
- Casos com repetição de requisição: 3; tentativas adicionais: 3.
- Respostas HTTP transitórias elegíveis a retry (429/5xx): 3.
- Casos com erro técnico registrado: 0.
- Letras em formato plain disponíveis no candidato aceito/instrumental: 22.
- Letras sincronizadas disponíveis no candidato aceito/instrumental: 12.
- Nenhum texto de letra foi gravado neste relatório ou no Parquet processado.

## Status finais

| final_status | len | percentual |
| --- | --- | --- |
| accepted_exact | 22 | 22.0 |
| ambiguous | 72 | 72.0 |
| not_found | 6 | 6.0 |

Contagem de candidatos retornados/deduplicados por composição: `{"min": 0, "median": 4.0, "mean": 6.92, "max": 21}`.

Combinações de status HTTP finais:

| http_status | len |
| --- | --- |
| /api/get:200;/api/search:200 | 93 |
| /api/get:404;/api/search:200 | 7 |

## Cobertura do desenho amostral

- Estratos período × quintil representados: 20 de 20.
- Gêneros representados: 25.
- Métodos de matching representados: 2.
- Perfis de versão representados: 1.
- Observação metodológica: o arredondamento proporcional nas células conjuntas gênero × método × versão preservou os 20 estratos primários e 25 gêneros, mas o smoke observado reteve somente dois métodos e apenas o perfil sem flag. Esse desequilíbrio marginal deve ser corrigido antes de qualquer repetição ou escala.

### Período × quintil

| period | popularity_quintile | len |
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

### Método de matching da base

| match_method | len |
| --- | --- |
| raw_exact | 98 |
| strict_normalized | 2 |

### Perfil de versão

| version_profile | len |
| --- | --- |
| original_sem_flag | 100 |

### Gênero

| genre | len |
| --- | --- |
| acoustic | 3 |
| alt-rock | 12 |
| black-metal | 5 |
| blues | 2 |
| chill | 1 |
| country | 11 |
| dance | 5 |
| death-metal | 10 |
| disco | 1 |
| electro | 1 |
| emo | 10 |
| folk | 5 |
| garage | 6 |
| goth | 1 |
| grindcore | 1 |
| hard-rock | 2 |
| hardcore | 8 |
| hip-hop | 3 |
| indie-pop | 4 |
| industrial | 1 |
| metal | 1 |
| metalcore | 1 |
| power-pop | 4 |
| ska | 1 |
| soul | 1 |

## Diferenças de duração nos aceitos

`{"n": 22, "min": 0.007000000000005002, "median": 0.14849999999999852, "mean": 0.2540779045454555, "max": 1.2780000000000058}`

## Limitações e decisão

O `/api/search` limita a resposta a 20 candidatos sem paginação. O protocolo aceita apenas um candidato único após igualdade normalizada exata de artista e título/título-base, compatibilidade de versão e tolerância de duração de até 10 segundos. Casos aproximados ficam em revisão; a primeira posição retornada nunca é aceita por si só. A licença MIT identificada refere-se ao código do LRCLIB, não confirma licença aberta de redistribuição das letras. Assim, este smoke mede viabilidade técnica, não autoriza escala nem publicação do conteúdo.

**Recomendação operacional: ajustar e repetir.** A alta ambiguidade e o desequilíbrio marginal do smoke devem ser tratados antes de novas consultas; as outras 1.900 composições não devem ser consultadas nesta versão.
