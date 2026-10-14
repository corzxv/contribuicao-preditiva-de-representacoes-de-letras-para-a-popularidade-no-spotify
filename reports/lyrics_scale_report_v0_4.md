# Coleta escalada de letras — v0.4

## Escopo

Foram processadas 15000 composições da coorte congelada e dos lotes de reserva eventualmente ativados. O pipeline aplicou exclusivamente `accepted_exact_unique` e `accepted_exact_equivalent`. Nenhuma popularidade do holdout foi carregada ou descrita.

## Resultado

- Aceitas: 10240 (68.27%).
- Desenvolvimento: 7648 aceitas.
- Holdout: 2592 aceitas.
- Reserva ativada: True.
- Lotes de reserva: [1, 2].
- Caches legados reutilizados: 293.
- Caches v0.4 existentes/reutilizados: 14707.
- Novas composições consultadas: 14707.
- Tentativas HTTP registradas: 37133; retries: 7133; erros técnicos: 0.

## Status finais

| Status | N |
|---|---:|
| accepted_exact_equivalent | 7126 |
| accepted_exact_unique | 3114 |
| ambiguous_distinct_lyrics | 3243 |
| ambiguous_metadata_conflict | 106 |
| ambiguous_search_truncated | 1 |
| instrumental | 109 |
| not_found | 644 |
| request_error | 657 |

Resultados individuais, candidatos, hashes, IDs e textos permanecem em área privada ignorada pelo Git. Nenhum texto ou trecho de letra aparece neste relatório.
