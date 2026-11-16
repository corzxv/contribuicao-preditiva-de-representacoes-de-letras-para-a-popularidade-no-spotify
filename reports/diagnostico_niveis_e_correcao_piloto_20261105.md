# Diagnóstico 31 concluído e correção do piloto 32 — 05/11/2026

## Execução confirmada de 31

Pesquisador executou a rotina integral de diagnóstico. Resumo completed=true,
77.535 faixas/21.893 componentes, suporte operacional aprovado em todas as
partições do esquema principal. Mínimos por classe/partição: 2.381 faixas e
1.322 componentes. Agente leu somente agregados e conferiu selos, sem refit ou
repetição da leitura integral. Resultado por faixa, sem ponderação adicional:

| Previsão antiga categorizada | Acurácia | Acurácia balanceada | Macro-F1 |
| --- | ---: | ---: | ---: |
| Baseline | 63,98% | 58,32% | 0,6019 |
| Tradicional | 64,42% | 58,84% | 0,6076 |
| Profundo | 65,41% | 60,18% | 0,6217 |
| Combinado | 65,54% | 60,42% | 0,6244 |
| Classe majoritária do treino externo | 43,94% | 33,33% | 0,2035 |

Combinado−Baseline: +2,11 pontos percentuais de acurácia balanceada;
Combinado−Profundo: +0,24 ponto. São pontos exploratórios das mesmas previsões
de regressão categorizadas, sem ajuste para classificação, probabilidades ou
inferência de significância. Não escolher cortes ou pesos por esses resultados.

## Falha e correção de 32

O Parquet v2 mantém popularity e duration_ms como large_string. A validação
anterior convertia popularidade em um array temporário, mas a ordenação e a
comparação ≥80 ainda usavam a coluna textual. Houve erro antes da seleção de
consultas ou exportação de fichas. Fontes, decisões e dados anteriores intactos.

v1.1 cria review_popularity_numeric Float64, valida finitude/inteiro/0..100 e usa
essa coluna na ordenação e na cauda. Popularidade original preservada. Teste com
9 e 100 verifica que o representante é escolhido numericamente; inválidos e nulos
bloqueiam sem exclusão. Fixture integral reproduz texto em popularidade/duração.

A tentativa v1 deixou somente selos/resumo incompleto; seus diretórios ficam
preservados. Como o código/selo mudou, v1.1 grava em pastas novas com sufixo v1_1.
Não é necessário apagar arquivos ou editar owners. A CLI e o comando são iguais.

## Verificação e continuidade

28 testes selecionados aprovados em 9,01 s; lint de src/scripts/tests e formatação
dos arquivos corrigidos conferidos. Registro em verificacao_correcao_piloto_20261105.json.
Nenhum treino, busca nova, índice ou novo embedding. 31 não precisa ser repetido.
Pesquisador deve executar novamente somente 32; preparação real v1.1 pendente.
Após isso, analisar as fichas e preparar o classificador conforme D-025.
