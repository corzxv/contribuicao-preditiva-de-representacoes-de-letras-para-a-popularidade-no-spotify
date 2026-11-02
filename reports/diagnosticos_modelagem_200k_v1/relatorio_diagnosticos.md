# Diagnósticos das previsões externas fixas

77535 faixas, 30 partes, métricas/contrastes reproduzidos; 21893 componentes. Nenhum modelo ajustado.

Subgrupos são exploratórios/descritivos; células com menos de 100 faixas ou 20 componentes omitem métricas públicas, sem excluir observações da análise principal. Idiomas são estimados e colisões históricas não restauram independência.

Remover um componente da avaliação mantém previsões/modelos fixos: não é leave-one-group-out com retreino, intervalo de confiança ou teste. Dependência dos ajustes da CV e incerteza do treinamento não são resolvidas aqui.

6/20 escolhas de alpha nos extremos da grade são diagnóstico de resolução; não autoriza expandir grade após ver teste. Previsões fora de 0..100 preservadas, sem clipping.
