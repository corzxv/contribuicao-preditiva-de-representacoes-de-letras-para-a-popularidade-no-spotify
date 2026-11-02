# Rodada v3

Escopo: diagnostic_only; concluída: True. Avaliação diagnóstica não aprova a base final.

Novas aceitações: 31 (classificador: 31; busca ampliada: 0). Aceitações anteriores agora inconclusivas: 2. Pares propostos: 205. Projeção no JSON refere-se somente aos três grupos sorteados e a decisões automáticas, sem precisão humana aferida.

| before | after | gain_stage | reason | len |
| --- | --- | --- | --- | --- |
| accepted | accepted | classifier | deterministic_identity_text_sequence | 98 |
| accepted | ambiguous | expanded_search | review_required | 2 |
| ambiguous | accepted | classifier | deterministic_identity_text_sequence | 31 |
| ambiguous | ambiguous | expanded_search | synced_requires_review | 1 |
| ambiguous | ambiguous | expanded_search | no_compatible_candidate_in_available_indexes | 56 |
| ambiguous | ambiguous | expanded_search | different_word_sequence_or_punctuation | 116 |
| ambiguous | ambiguous | expanded_search | plain_synced_content_conflict | 3 |
| ambiguous | ambiguous | expanded_search | operational_limit:artist_block_limit | 89 |
| ambiguous | ambiguous | expanded_search | instrumental_text_conflict | 4 |
| not_found | ambiguous | expanded_search | operational_limit:artist_block_limit | 19 |
| not_found | ambiguous | expanded_search | review_required | 12 |
| not_found | not_found | expanded_search | no_compatible_candidate_in_available_indexes | 569 |

Scores apenas recuperam candidatos; aceite aproximado desativado. Precisão ainda não medida. Custo de escala é extrapolação por grupo, sem incluir validação/exportação; censura por tempo e grupos não avaliados impedem previsão completa. Índices restritos não provam ausência no dump. Nenhuma nova varredura proposta automaticamente.
