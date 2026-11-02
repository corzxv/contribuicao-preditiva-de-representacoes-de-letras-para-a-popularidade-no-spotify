# Teste complementar do Piloto de Letras — v0.1.2

## Escopo e salvaguardas

O teste permaneceu restrito ao `development_train`, preservou a coorte original de 2.000 composições e não consultou novamente as 100 músicas do smoke anterior. A nova amostra é intencional e dirigida a estratos sub-representados; portanto, **não é uma amostra aleatória** e seus percentuais não devem ser interpretados como estimativas da coorte completa. Não houve consulta ao holdout, treinamento, embeddings, fuzzy matching ou publicação de texto de letras.

## Auditoria offline das 16 buscas limitadas

- Casos com exatamente 20 resultados em `/api/search`: 16.
- Casos com retorno exato compatível e letra em `/api/get`: 16.
- Aceitações que dependiam exclusivamente da busca truncada: 0.
- Aceitos v0.1.1 preservados: 66 de 66.
- Aceitos v0.1.1 reclassificados: 0.

Regra v0.1.2: quando a busca retorna exatamente 20 resultados, a equivalência estrita entre os 20 candidatos não basta para aceitar. Sem um `/api/get` exato, compatível e com `plainLyrics`, o caso recebe `ambiguous_search_truncated`. Havendo esse retorno exato, a aceitação só permanece se nenhum candidato elegível tiver fingerprint estrito distinto.

Status finais dos 16 casos:

| status | n |
| --- | --- |
| accepted_exact_equivalent | 7 |
| ambiguous_distinct_lyrics | 9 |

## Inventário das 1.900 composições inéditas

Método de matching:

| match_method | n |
| --- | --- |
| base_title_version_compatible | 12 |
| conservative_normalized | 118 |
| raw_exact | 1391 |
| strict_normalized | 379 |

Flags de versão (uma composição pode ter mais de uma flag):

| flag | n |
| --- | --- |
| remaster | 2 |
| remix | 0 |
| live | 9 |
| acoustic | 0 |
| radio_edit | 0 |
| mono_stereo | 0 |
| instrumental | 0 |
| demo | 1 |
| karaoke | 0 |

- Com qualquer flag de versão: 12.

Período:

| periodo | n |
| --- | --- |
| 2000-2005 | 305 |
| 2006-2011 | 388 |
| 2012-2017 | 770 |
| 2018-2023 | 437 |

Quintil de popularidade, usado somente para balanceamento amostral:

| quintil | n |
| --- | --- |
| Q1 | 382 |
| Q2 | 399 |
| Q3 | 394 |
| Q4 | 358 |
| Q5 | 367 |

Gênero:

| genero | n |
| --- | --- |
| acoustic | 49 |
| alt-rock | 110 |
| ambient | 18 |
| black-metal | 54 |
| blues | 46 |
| chill | 45 |
| classical | 5 |
| club | 9 |
| comedy | 6 |
| country | 90 |
| dance | 72 |
| dancehall | 19 |
| death-metal | 84 |
| deep-house | 10 |
| disco | 25 |
| drum-and-bass | 6 |
| dub | 15 |
| dubstep | 2 |
| edm | 18 |
| electro | 29 |
| electronic | 15 |
| emo | 115 |
| folk | 67 |
| french | 12 |
| funk | 44 |
| garage | 59 |
| german | 13 |
| gospel | 10 |
| goth | 41 |
| grindcore | 15 |
| groove | 18 |
| hard-rock | 58 |
| hardcore | 83 |
| hardstyle | 4 |
| heavy-metal | 11 |
| hip-hop | 65 |
| house | 3 |
| indian | 5 |
| indie-pop | 53 |
| industrial | 39 |
| jazz | 18 |
| k-pop | 16 |
| metal | 43 |
| metalcore | 30 |
| new-age | 1 |
| opera | 3 |
| piano | 16 |
| pop | 19 |
| power-pop | 37 |
| progressive-house | 7 |
| psych-rock | 34 |
| punk | 36 |
| punk-rock | 19 |
| rock | 15 |
| rock-n-roll | 6 |
| sad | 1 |
| show-tunes | 9 |
| singer-songwriter | 38 |
| ska | 29 |
| songwriter | 1 |
| soul | 45 |
| swedish | 24 |
| techno | 2 |
| trance | 4 |
| trip-hop | 5 |

## Amostra complementar determinística

- Semente: 20260927.
- Selecionadas: 47 (teto autorizado: 60).
- Split observado: development_train.
- Nenhuma música pertence às 100 já consultadas.
- Quotas insuficientes não foram preenchidas com `raw_exact`.

Seleção por motivo principal, sem duplicação entre grupos:

| motivo | n |
| --- | --- |
| any_version_flag | 5 |
| base_title_version_compatible | 12 |
| conservative_normalized | 15 |
| strict_normalized | 15 |

A disponibilidade bruta e a sobreposição explicam o total inferior a 60: havia 12 casos `base_title_version_compatible` e 12 casos com alguma flag de versão, dos quais parte já pertence ao grupo `base_title`.

## Resultados complementares observados

- Composições consultadas: 47.
- Cobertura automática estrita: 70.21%.
- Cobertura bruta com ao menos um candidato: 97.87%.
- Buscas com exatamente 20 resultados: 12.
- Tentativas HTTP: 94; retries adicionais: 0.
- Erros técnicos: 0.
- Tempo observado nesta execução: 81.833 s.

Status:

| status | n |
| --- | --- |
| accepted_exact_equivalent | 23 |
| accepted_exact_unique | 10 |
| ambiguous_distinct_lyrics | 11 |
| instrumental | 2 |
| not_found | 1 |

Estatísticas de candidatos após união e deduplicação técnica:

`{"maximum": 21, "mean": 8.723404, "median": 5.0, "minimum": 0, "total": 410}`

Resultados por método de matching:

`{"base_title_version_compatible": {"accepted_exact_equivalent": 7, "accepted_exact_unique": 1, "ambiguous_distinct_lyrics": 3, "not_found": 1}, "conservative_normalized": {"accepted_exact_equivalent": 8, "accepted_exact_unique": 3, "ambiguous_distinct_lyrics": 7}, "raw_exact": {"accepted_exact_equivalent": 1}, "strict_normalized": {"accepted_exact_equivalent": 7, "accepted_exact_unique": 6, "ambiguous_distinct_lyrics": 1, "instrumental": 2}}`

Resultados por motivo amostral:

`{"any_version_flag": {"accepted_exact_equivalent": 2, "accepted_exact_unique": 3}, "base_title_version_compatible": {"accepted_exact_equivalent": 7, "accepted_exact_unique": 1, "ambiguous_distinct_lyrics": 3, "not_found": 1}, "conservative_normalized": {"accepted_exact_equivalent": 7, "accepted_exact_unique": 1, "ambiguous_distinct_lyrics": 7}, "strict_normalized": {"accepted_exact_equivalent": 7, "accepted_exact_unique": 5, "ambiguous_distinct_lyrics": 1, "instrumental": 2}}`

Resultados por perfil de versão:

`{"demo": {"accepted_exact_equivalent": 1}, "live": {"accepted_exact_equivalent": 4, "accepted_exact_unique": 3, "ambiguous_distinct_lyrics": 1, "not_found": 1}, "original_sem_flag": {"accepted_exact_equivalent": 17, "accepted_exact_unique": 6, "ambiguous_distinct_lyrics": 10, "instrumental": 2}, "remaster": {"accepted_exact_equivalent": 1, "accepted_exact_unique": 1}}`

Resultados com e sem qualquer flag de versão:

`{"False": {"accepted_exact_equivalent": 17, "accepted_exact_unique": 6, "ambiguous_distinct_lyrics": 10, "instrumental": 2}, "True": {"accepted_exact_equivalent": 6, "accepted_exact_unique": 4, "ambiguous_distinct_lyrics": 1, "not_found": 1}}`

Resultados por tipo de flag observado:

`{"demo": {"accepted_exact_equivalent": 1}, "live": {"accepted_exact_equivalent": 4, "accepted_exact_unique": 3, "ambiguous_distinct_lyrics": 1, "not_found": 1}, "original_sem_flag": {"accepted_exact_equivalent": 17, "accepted_exact_unique": 6, "ambiguous_distinct_lyrics": 10, "instrumental": 2}, "remaster": {"accepted_exact_equivalent": 1, "accepted_exact_unique": 1}}`

Resultados por período e quintil são apresentados somente de forma descritiva:

- Período: `{"2000-2005": {"accepted_exact_equivalent": 7, "accepted_exact_unique": 2, "ambiguous_distinct_lyrics": 3}, "2006-2011": {"accepted_exact_equivalent": 3, "accepted_exact_unique": 2, "ambiguous_distinct_lyrics": 5, "instrumental": 1, "not_found": 1}, "2012-2017": {"accepted_exact_equivalent": 10, "accepted_exact_unique": 2}, "2018-2023": {"accepted_exact_equivalent": 3, "accepted_exact_unique": 4, "ambiguous_distinct_lyrics": 3, "instrumental": 1}}`
- Quintil: `{"Q1": {"accepted_exact_equivalent": 5, "accepted_exact_unique": 3, "ambiguous_distinct_lyrics": 1, "not_found": 1}, "Q2": {"accepted_exact_equivalent": 3, "accepted_exact_unique": 5, "ambiguous_distinct_lyrics": 1}, "Q3": {"accepted_exact_equivalent": 5, "accepted_exact_unique": 2, "ambiguous_distinct_lyrics": 2}, "Q4": {"accepted_exact_equivalent": 5, "ambiguous_distinct_lyrics": 2, "instrumental": 2}, "Q5": {"accepted_exact_equivalent": 5, "ambiguous_distinct_lyrics": 5}}`

## Leitura conjunta, sem inferência aleatória

O smoke original e o teste complementar podem ser somados apenas para descrever o que foi efetivamente consultado. A seleção complementar super-representa métodos raros e flags de versão; ela não corrige o desenho amostral do smoke nem autoriza extrapolação para as outras composições.

## Privacidade, imutabilidade e decisão

- Cache privado final: 147 arquivos, esperado 147.
- Arquivos privados rastreados pelo Git: 0.
- Campos textuais proibidos nos Parquets públicos: [].
- Campos de sucesso usados na decisão de matching: [].
- Hashes imutáveis preservados: True.
- Split original preservado: True.

**Recomendação final: escalar para o restante da coorte de 2.000.** Esta é uma recomendação analítica; nenhuma escala automática foi iniciada.
