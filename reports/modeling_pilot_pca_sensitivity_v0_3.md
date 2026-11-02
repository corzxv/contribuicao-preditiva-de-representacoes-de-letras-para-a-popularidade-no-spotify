# Sensibilidade PCA 90% — Modelagem piloto v0.3

A análise principal usa as 384 dimensões. A PCA foi ajustada separadamente no treino de cada fold, somente sobre o bloco de embeddings, sem alvo e sem variáveis categóricas. O percentual de 90% foi fixado antes dos resultados externos.

| Algoritmo | Bloco | MAE raw | MAE PCA | Δ MAE PCA−raw | RMSE raw | RMSE PCA | Componentes PCA médios |
|---|---|---|---|---|---|---|---|
| elastic_net | deep | 9.031 | 7.800 | -1.230 | 11.691 | 10.109 | 163 |
| elastic_net | combined | 8.897 | 8.859 | -0.038 | 11.559 | 11.503 | 163 |
| hist_gradient_boosting | deep | 8.118 | 8.067 | -0.051 | 10.667 | 10.632 | 163 |
| hist_gradient_boosting | combined | 8.086 | 8.065 | -0.021 | 10.606 | 10.568 | 163 |

Componentes não são interpretados causalmente. A contagem exibida é a média arredondada dos cinco ajustes externos; a contagem por fold está no CSV agregado de métricas.
