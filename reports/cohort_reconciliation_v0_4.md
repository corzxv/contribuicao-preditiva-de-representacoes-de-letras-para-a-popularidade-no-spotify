# Reconciliação documental da coorte final v0.4

Esta nota acrescenta evidências aos registros originais, preservados integralmente.

`technical_errors` conta resultados com `technical_error` não nulo. O campo vem de `_safe_attempt_error` (lyrics_pilot.py), que registra exceções com `error_type` nas tentativas; não conta respostas HTTP de erro. Foram 0 exceções registradas e 657 resultados finais `request_error`. Os padrões HTTP desses resultados constam no JSON agregado anexo. Uma resposta HTTP 503 pode resultar em `request_error` sem exceção de transporte; os dois contadores medem eventos diferentes.

O total de chunks somado por composição é 17984, isto é, 1.75625 × 10240. Há 17978 chunks por hash único; 6 chunks pertencem a composições adicionais com texto normalizado idêntico. Dos chunks únicos, 385 correspondem a vetores do piloto reutilizados e 17593 foram efetivamente codificados na v0.4. A função `_encode_unique_records` deduplica por hash antes de codificar. Portanto, 17.593 é a codificação nova, não a soma por composição.

O intervalo de parede da primeira requisição até a consolidação final foi 112169.952 s; inclui execução, pausas, retomadas e consolidação. O campo original `duration_seconds=357.285` mede somente a última chamada idempotente de consolidação, não toda a coleta nem tempo ativo acumulado. Não há registro suficiente para reconstruir exatamente todo o tempo ativo acumulado.

Auditoria: desenvolvimento 7648, holdout 2592; artistas compartilhados 0; composições compartilhadas 0; hashes normalizados de letras compartilhados 0. Representantes correspondem integralmente ao lookup congelado. Hashes de base, split e oito artefatos privados conferem; NaN 0; infinito 0. Nenhum alvo do holdout foi carregado.
